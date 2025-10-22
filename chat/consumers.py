# chat/consumers.py (TÜM DÜZELTMELER YAPILMIŞ NİHAİ HALİ)

import json
from urllib.parse import unquote_plus
# <<< YENİ: Standart datetime kütüphanesinden timezone import edildi >>>
from datetime import timezone as dt_timezone
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer 

from .models import Room, Message, UserProfile, Conversation, Reaction, UserChatStatus
from .serializers import MessageSerializer

ACTIVE_VOICE_USERS = {}
ACTIVE_CHAT_USERS = {}
ACTIVE_GLOBAL_USERS = {}
TYPING_USERS = {}
GLOBAL_STATUS_GROUP = 'global_voice_status'
GLOBAL_USER_GROUP = 'global_user_status'  


def get_unread_counts_for_user(username):
    """Belirtilen kullanıcı için okunmamış oda ve DM mesaj sayılarını hesaplar."""
    try:
        user = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return {}

    unread_counts = {}
    
    rooms = Room.objects.all()
    for room in rooms:
        try:
            status = UserChatStatus.objects.get(user=user, room=room)
            last_read = status.last_read_timestamp
        except UserChatStatus.DoesNotExist:
            # <<< DEĞİŞİKLİK: Hatalı olan timezone.utc, dt_timezone.utc ile düzeltildi >>>
            last_read = timezone.datetime.min.replace(tzinfo=dt_timezone.utc)
        
        count = Message.objects.filter(
            room=room, 
            timestamp__gt=last_read
        ).exclude(username=username).count()
        
        if count > 0:
            unread_counts[f'room-{room.slug}'] = count

    conversations = user.conversations.all()
    for conv in conversations:
        try:
            status = UserChatStatus.objects.get(user=user, conversation=conv)
            last_read = status.last_read_timestamp
        except UserChatStatus.DoesNotExist:
            # <<< DEĞİŞİKLİK: Hatalı olan timezone.utc, dt_timezone.utc ile düzeltildi >>>
            last_read = timezone.datetime.min.replace(tzinfo=dt_timezone.utc)
            
        count = Message.objects.filter(
            conversation=conv, 
            timestamp__gt=last_read
        ).exclude(username=username).count()
        
        if count > 0:
            unread_counts[f'dm-{conv.id}'] = count
            
    return unread_counts


@transaction.atomic
def create_message_and_get_data(target_model_instance, username, content=None, image_file=None, reply_to_id=None):
    params = { 'username': username, 'content': content if content else None, 'image': image_file if image_file else None }
    if isinstance(target_model_instance, Room): params['room'] = target_model_instance
    elif isinstance(target_model_instance, Conversation): params['conversation'] = target_model_instance
    else: raise TypeError("Hedef Room veya Conversation olmalı")

    if reply_to_id:
        try:
            params['reply_to'] = Message.objects.get(id=reply_to_id)
        except Message.DoesNotExist:
            pass

    msg_instance = Message.objects.create(**params)
    print(f"[DB KAYIT BAŞARILI] Hedef: '{target_model_instance}', Kullanıcı: '{username}'")
    return MessageSerializer(msg_instance).data

def create_room_sync(slug, channel_type):
    if not slug or slug == 'genel': return None
    try: return Room.objects.create(name=slug, slug=slug, channel_type=channel_type)
    except Exception: return None

def delete_room_sync(slug):
    if slug == 'genel': return 0
    deleted_count, _ = Room.objects.filter(slug=slug).delete()
    return deleted_count

def get_all_room_data_sync():
    all_rooms = list(Room.objects.values('slug', 'channel_type').order_by('slug'))
    general_room = next((r for r in all_rooms if r['slug'] == 'genel'), None)
    other_rooms = [r for r in all_rooms if r['slug'] != 'genel']
    if general_room: return [general_room] + other_rooms
    return other_rooms

def update_user_profile_sync(username):
    try:
        user_profile, created = UserProfile.objects.get_or_create(username=username)
        user_profile.last_seen = timezone.now()
        user_profile.save()
        return user_profile
    except Exception as e:
        print(f"[HATA] Kullanıcı profili güncellenemedi: {username}, Hata: {e}")
        return None

def update_global_user_status(username, action):
    old_count = ACTIVE_GLOBAL_USERS.get(username, 0)
    
    if action == 'connect':
        ACTIVE_GLOBAL_USERS[username] = old_count + 1
        is_online_changed = old_count == 0 and ACTIVE_GLOBAL_USERS[username] == 1
    elif action == 'disconnect':
        if old_count > 0:
            ACTIVE_GLOBAL_USERS[username] = old_count - 1
        is_online_changed = old_count > 0 and ACTIVE_GLOBAL_USERS[username] <= 0
        if ACTIVE_GLOBAL_USERS[username] <= 0:
            if username in ACTIVE_GLOBAL_USERS:
                del ACTIVE_GLOBAL_USERS[username]
    else:
        return
        
    if is_online_changed:
        online_users = list(ACTIVE_GLOBAL_USERS.keys())
        async_to_sync(get_channel_layer().group_send)(
            GLOBAL_USER_GROUP,
            {'type': 'online_user_list_update', 'users': online_users}
        )

class ChatConsumer(WebsocketConsumer):
    def get_room(self, room_slug):
        try: return Room.objects.get(slug=room_slug)
        except Room.DoesNotExist: return None
        
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        query_params = dict(p.split('=') for p in self.scope['query_string'].decode().split('&') if '=' in p)
        self.username = unquote_plus(query_params.get('username', 'Misafir'))
        if not self.get_room(self.room_name): self.close(); return
        
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        
        if self.room_name not in ACTIVE_CHAT_USERS: ACTIVE_CHAT_USERS[self.room_name] = set()
        ACTIVE_CHAT_USERS[self.room_name].add(self.username)
        
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {'type': 'system_message_handler', 'message': f'{self.username} kanala katıldı.'}
        )

        self.broadcast_chat_user_list()
        update_global_user_status(self.username, 'connect')
        async_to_sync(self.channel_layer.group_add)(GLOBAL_USER_GROUP, self.channel_name)
        
        self.send(text_data=json.dumps({ 'type': 'online_user_list_update', 'online_users': list(ACTIVE_GLOBAL_USERS.keys()) }))
        update_user_profile_sync(self.username)

    def disconnect(self, close_code):
        if self.room_name in ACTIVE_CHAT_USERS and self.username in ACTIVE_CHAT_USERS[self.room_name]:
            ACTIVE_CHAT_USERS[self.room_name].discard(self.username)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {'type': 'system_message_handler', 'message': f'{self.username} kanaldan ayrıldı.'}
            )
            self.broadcast_chat_user_list()

        update_global_user_status(self.username, 'disconnect')
        async_to_sync(self.channel_layer.group_discard)(GLOBAL_USER_GROUP, self.channel_name)
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'edit_message':
            try:
                message = Message.objects.select_related('reply_to').prefetch_related('reactions').get(id=data.get('message_id'))
                if message.username == self.username:
                    message.content = data.get('new_content')
                    message.is_edited = True
                    message.save()
                    message_data = MessageSerializer(message).data
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {'type': 'message_updated_handler', 'message': message_data}
                    )
            except Message.DoesNotExist: pass

        elif message_type == 'delete_message':
            try:
                message = Message.objects.get(id=data.get('message_id'))
                if message.username == self.username:
                    message_id = message.id
                    message.delete()
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {'type': 'message_deleted_handler', 'message_id': message_id}
                    )
            except Message.DoesNotExist: pass
        
        elif message_type == 'toggle_reaction':
            try:
                message = Message.objects.select_related('reply_to').prefetch_related('reactions').get(id=data.get('message_id'))
                emoji = data.get('emoji')
                reaction, created = Reaction.objects.get_or_create(message=message, username=self.username, emoji=emoji)
                if not created:
                    reaction.delete()
                
                message.refresh_from_db() 
                message_data = MessageSerializer(message).data
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {'type': 'message_updated_handler', 'message': message_data}
                )
            except Message.DoesNotExist: pass

        elif message_type == 'chat_message':
            room_obj = self.get_room(self.room_name)
            if room_obj:
                try:
                    message_data = create_message_and_get_data(
                        room_obj, 
                        data.get('username'), 
                        content=data.get('message'),
                        reply_to_id=data.get('reply_to')
                    )
                    if data.get('temp_id'): message_data['temp_id'] = data.get('temp_id') 

                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'chat_message_handler', **message_data})
                    async_to_sync(self.channel_layer.group_send)(GLOBAL_STATUS_GROUP, {'type': 'global_message_notification', **message_data, 'room_slug': self.room_name})
                except Exception as e:
                    print(f"[HATA] Oda mesajı kaydedilirken hata: {e}")
            
        elif message_type == 'typing_start':
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'typing_status_handler', 'username': self.username, 'is_typing': True})
        elif message_type == 'typing_stop':
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'typing_status_handler', 'username': self.username, 'is_typing': False})

    def system_message_handler(self, event):
        self.send(text_data=json.dumps({'type': 'system_message', 'message': event['message']}))

    def message_updated_handler(self, event):
        self.send(text_data=json.dumps({'type': 'message_updated', 'message': event['message']}))

    def message_deleted_handler(self, event):
        self.send(text_data=json.dumps({'type': 'message_deleted', 'message_id': event['message_id']}))

    def typing_status_handler(self, event):
        self.send(text_data=json.dumps({ 'type': 'typing_status_update', 'username': event['username'], 'is_typing': event['is_typing'] }))

    def chat_message_handler(self, event):
        payload = {k: v for k, v in event.items() if k != 'type'}
        self.send(text_data=json.dumps({ 'type': 'chat', **payload }))

    def broadcast_chat_user_list(self):
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'chat_user_list_update', 'users': list(ACTIVE_CHAT_USERS.get(self.room_name, []))})
        
    def chat_user_list_update(self, event):
        self.send(text_data=json.dumps({'type': 'chat_user_list_update', 'users': event['users']}))
        
    def room_deleted_notification(self, event): self.close()

    def online_user_list_update(self, event):
        self.send(text_data=json.dumps({'type': 'online_user_list_update', 'online_users': event['users']}))

class DMConsumer(WebsocketConsumer):
    def get_conversation(self, conversation_id):
        try: return Conversation.objects.prefetch_related('participants').get(id=conversation_id)
        except Conversation.DoesNotExist: return None

    def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'dm_{self.conversation_id}'
        query_params = dict(p.split('=') for p in self.scope['query_string'].decode().split('&') if '=' in p)
        self.username = unquote_plus(query_params.get('username', None))
        if not self.username: self.close(); return
        self.conversation = self.get_conversation(self.conversation_id)
        if not self.conversation or not self.conversation.participants.filter(username=self.username).exists(): self.close(); return
        
        async_to_sync(self.channel_layer.group_add)(self.conversation_group_name, self.channel_name)
        self.accept()
        
        update_global_user_status(self.username, 'connect')
        async_to_sync(self.channel_layer.group_add)(GLOBAL_USER_GROUP, self.channel_name)
        self.send(text_data=json.dumps({ 'type': 'online_user_list_update', 'online_users': list(ACTIVE_GLOBAL_USERS.keys()) }))
        update_user_profile_sync(self.username)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.conversation_group_name, self.channel_name)
        update_global_user_status(self.username, 'disconnect')
        async_to_sync(self.channel_layer.group_discard)(GLOBAL_USER_GROUP, self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'typing_start':
            async_to_sync(self.channel_layer.group_send)(self.conversation_group_name, {'type': 'dm_typing_status_handler', 'username': self.username, 'is_typing': True, 'sender_channel_name': self.channel_name})
        elif message_type == 'typing_stop':
            async_to_sync(self.channel_layer.group_send)(self.conversation_group_name, {'type': 'dm_typing_status_handler', 'username': self.username, 'is_typing': False, 'sender_channel_name': self.channel_name})
        
        elif message_type == 'dm_message':
            if self.conversation:
                try:
                    message_data = create_message_and_get_data(
                        self.conversation,
                        data.get('username'),
                        content=data.get('message'),
                        reply_to_id=data.get('reply_to')
                    )
                    if data.get('temp_id'): message_data['temp_id'] = data.get('temp_id')
                    
                    async_to_sync(self.channel_layer.group_send)(self.conversation_group_name, {'type': 'dm_message_handler', **message_data})
                    async_to_sync(self.channel_layer.group_send)(GLOBAL_STATUS_GROUP, {'type': 'global_message_notification', **message_data, 'conversation_id': self.conversation_id})
                except Exception as e:
                    print(f"[HATA] DM mesajı hatası: {e}")

    def dm_typing_status_handler(self, event):
        if self.channel_name != event.get('sender_channel_name'):
            self.send(text_data=json.dumps({
                'type': 'typing_status_update',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    def dm_message_handler(self, event):
        payload = {k: v for k, v in event.items() if k != 'type'}
        self.send(text_data=json.dumps({ 'type': 'dm', **payload }))

    def online_user_list_update(self, event):
        self.send(text_data=json.dumps({'type': 'online_user_list_update', 'online_users': event['users']}))

class VoiceConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'voice_{self.room_name}'
        query_params = {key: value for key, value in (param.split('=', 1) for param in self.scope['query_string'].decode().split('&') if '=' in param)}
        self.username = unquote_plus(query_params.get('username', 'Misafir'))
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        if self.room_name not in ACTIVE_VOICE_USERS: ACTIVE_VOICE_USERS[self.room_name] = set()
        ACTIVE_VOICE_USERS[self.room_name].add(self.username)
        self.send_global_voice_status()
        self.accept()

    def disconnect(self, close_code):
        if self.username in ACTIVE_VOICE_USERS.get(self.room_name, set()):
            ACTIVE_VOICE_USERS[self.room_name].discard(self.username)
            if not ACTIVE_VOICE_USERS[self.room_name]: del ACTIVE_VOICE_USERS[self.room_name]
        self.send_global_voice_status()
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        
    def send_global_voice_status(self):
        async_to_sync(self.channel_layer.group_send)(GLOBAL_STATUS_GROUP, {'type': 'voice_state_update_handler', 'rooms': {room_name: list(users) for room_name, users in ACTIVE_VOICE_USERS.items()}})

    def receive(self, text_data):
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'voice_signal_handler', 'signal_data': json.loads(text_data), 'sender_channel_name': self.channel_name})
    
    def voice_signal_handler(self, event):
        if event['sender_channel_name'] != self.channel_name: self.send(text_data=json.dumps(event['signal_data']))
        
    def room_deleted_notification(self, event): self.close()

class GlobalStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = GLOBAL_STATUS_GROUP
        
        query_params = dict(p.split('=') for p in self.scope['query_string'].decode().split('&') if '=' in p)
        self.username = unquote_plus(query_params.get('username', None))

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name) 
        async_to_sync(self.channel_layer.group_add)(GLOBAL_USER_GROUP, self.channel_name) 
        self.accept()

        if self.username:
            self.send_initial_status(self.username)

    def disconnect(self, close_code): 
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        async_to_sync(self.channel_layer.group_discard)(GLOBAL_USER_GROUP, self.channel_name)

    def voice_state_update_handler(self, event):
        self.send(text_data=json.dumps({'type': 'voice_state_update', 'initial_load': True, 'rooms': event['rooms']}))
        
    def online_user_list_update(self, event):
        self.send(text_data=json.dumps({'type': 'online_user_list_update', 'online_users': event['users']}))
    
    def user_profile_update_handler(self, event):
        self.send(text_data=json.dumps({
            'type': 'user_profile_update',
            'user_data': event['user_data']
        }))

    def global_message_notification(self, event):
        payload = {k: v for k, v in event.items() if k != 'type'}
        self.send(text_data=json.dumps({ 'type': 'global_message_notification', **payload }))

    def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'add_room':
            if create_room_sync(data.get('room_slug'), data.get('channel_type')): self.broadcast_room_list_update()
        elif data.get('type') == 'remove_room':
            if delete_room_sync(data.get('room_slug')) > 0:
                self.broadcast_room_list_update()
                async_to_sync(self.channel_layer.group_send)(f'chat_{data.get("room_slug")}', {'type': 'room_deleted_notification'})
                async_to_sync(self.channel_layer.group_send)(f'voice_{data.get("room_slug")}', {'type': 'room_deleted_notification'})

    def broadcast_room_list_update(self):
        room_data = get_all_room_data_sync()
        async_to_sync(self.channel_layer.group_send)(self.group_name, {'type': 'room_list_update', 'rooms': room_data})

    def room_list_update(self, event):
        self.send(text_data=json.dumps({'type': 'room_list_update', 'rooms': event['rooms']}))

    def send_initial_status(self, username):
        room_data = get_all_room_data_sync()
        self.send(text_data=json.dumps({'type': 'room_list_update', 'rooms': room_data}))
        
        initial_voice_status = {'type': 'voice_state_update', 'initial_load': True, 'rooms': {room: list(users) for room, users in ACTIVE_VOICE_USERS.items()}}
        self.send(text_data=json.dumps(initial_voice_status))
        
        initial_online_status = {'type': 'online_user_list_update', 'online_users': list(ACTIVE_GLOBAL_USERS.keys())}
        self.send(text_data=json.dumps(initial_online_status))
        
        unread_data = get_unread_counts_for_user(username)
        self.send(text_data=json.dumps({'type': 'unread_counts_update', 'counts': unread_data}))