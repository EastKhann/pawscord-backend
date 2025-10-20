import json
from urllib.parse import unquote_plus
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
import datetime
# Lütfen .models dosyanızın doğru yolda olduğundan emin olun
from .models import Room, Message, UserProfile

# ===================================================================
# GLOBAL STATE: AKTİF KULLANICILARIN TAKİBİ
# ===================================================================
ACTIVE_VOICE_USERS = {}
ACTIVE_CHAT_USERS = {}  # Metin sohbet odalarındaki kullanıcıları takip etmek için
TYPING_USERS = {}
GLOBAL_STATUS_GROUP = 'global_voice_status'

# ===================================================================
# 1. CHAT CONSUMER (Metin Mesajları ve Kullanıcı Listesi)
# ===================================================================

class ChatConsumer(WebsocketConsumer):

    # --- YARDIMCI FONKSİYONLAR ---
    def get_client_ip(self, scope):
        if 'client' in scope and len(scope['client']) > 0:
            return scope['client'][0]
        return None

    def resolve_username_sync(self, ip_address, requested_username):
        try:
            profile = UserProfile.objects.get(ip_address=ip_address)
            
            if profile.username != requested_username:
                profile.username = requested_username
                profile.save()
            
            return requested_username, True
        
        except UserProfile.DoesNotExist:
            try:
                UserProfile.objects.get(username=requested_username)
                return requested_username, False
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    ip_address=ip_address,
                    username=requested_username
                )
                return requested_username, True

    def get_room(self, room_slug):
        try:
            return Room.objects.get(slug=room_slug)
        except Room.DoesNotExist:
            try:
                return Room.objects.get(slug='genel')
            except Room.DoesNotExist:
                print("HATA: Ne istenen oda ne de 'genel' odası veritabanında bulunamadı!")
                return None

    # ------------------------------------------------------------------
    # CONNECT & DISCONNECT
    # ------------------------------------------------------------------
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        query_string = self.scope.get('query_string', b'').decode()
        query_params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value

        requested_username = query_params.get('username', 'Misafir')
        self.username = unquote_plus(requested_username)
        
        client_ip = self.get_client_ip(self.scope)

        self.username, is_ip_matched = async_to_sync(sync_to_async(self.resolve_username_sync))(client_ip, self.username)
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        if self.room_name not in TYPING_USERS:
            TYPING_USERS[self.room_name] = set()

        self.accept()
        
        # Chat kullanıcı listesi yönetimi
        if self.room_name not in ACTIVE_CHAT_USERS:
            ACTIVE_CHAT_USERS[self.room_name] = set()
        ACTIVE_CHAT_USERS[self.room_name].add(self.username)
        self.broadcast_chat_user_list()


    def disconnect(self, close_code):
        if self.username in TYPING_USERS.get(self.room_name, set()):
            self.broadcast_typing_stop()
        
        # Chat kullanıcı listesi yönetimi
        if self.room_name in ACTIVE_CHAT_USERS and self.username in ACTIVE_CHAT_USERS[self.room_name]:
            ACTIVE_CHAT_USERS[self.room_name].discard(self.username)
            if not ACTIVE_CHAT_USERS[self.room_name]:
                del ACTIVE_CHAT_USERS[self.room_name]
            self.broadcast_chat_user_list()

        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # ------------------------------------------------------------------
    # RECEIVE
    # ------------------------------------------------------------------

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            message = text_data_json.get('message', 'Boş Mesaj')
            username = text_data_json.get('username', 'Misafir')
            
            if self.username in TYPING_USERS.get(self.room_name, set()):
                self.broadcast_typing_stop()

            def create_message_sync(room_name_slug, username, message):
                room_obj = self.get_room(room_name_slug)
                if room_obj:
                    msg_instance = Message.objects.create(
                        room=room_obj,
                        username=username,
                        content=message
                    )
                    return msg_instance.timestamp.isoformat()
                return None
            
            timestamp_iso = async_to_sync(sync_to_async(create_message_sync))(self.room_name, username, message)
            
            if timestamp_iso:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                        'timestamp': timestamp_iso
                    }
                )

        elif message_type == 'typing_start':
            TYPING_USERS[self.room_name].add(self.username)
            self.broadcast_typing_update()

        elif message_type == 'typing_stop':
            self.broadcast_typing_stop()
            
        elif message_type == 'mark_read':
            self.mark_room_as_read()

    # ------------------------------------------------------------------
    # YAYIN METODLARI
    # ------------------------------------------------------------------
    
    def broadcast_chat_user_list(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_user_list_update',
                'users': list(ACTIVE_CHAT_USERS.get(self.room_name, set())),
            }
        )

    def broadcast_typing_update(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'typing_update',
                'users': list(TYPING_USERS.get(self.room_name, set())),
            }
        )

    def broadcast_typing_stop(self):
        if self.username in TYPING_USERS.get(self.room_name, set()):
            TYPING_USERS[self.room_name].discard(self.username)
            self.broadcast_typing_update()
            
    def chat_user_list_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'chat_user_list_update',
            'users': event['users'],
        }))
    
    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event.get('timestamp')
        }))

    def typing_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'typing_update',
            'users': event['users'],
        }))

    def voice_state_update(self, event):
        pass

    def mark_room_as_read(self):
        print(f"[READ] User {self.username} marked {self.room_name} as read.")
        pass

# ===================================================================
# 2. VOICE CONSUMER (Değişiklik yok)
# ===================================================================

class VoiceConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'voice_%s' % self.room_name
        query_string = self.scope.get('query_string', b'').decode()
        query_params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
        requested_username = query_params.get('username', 'Misafir')
        self.username = unquote_plus(requested_username)
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        if self.room_name not in ACTIVE_VOICE_USERS:
            ACTIVE_VOICE_USERS[self.room_name] = set()
        ACTIVE_VOICE_USERS[self.room_name].add(self.username)
        voice_update_event = {'type': 'voice_state_update', 'room_name': self.room_name, 'users': list(ACTIVE_VOICE_USERS[self.room_name]), 'action': 'join'}
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, voice_update_event)
        async_to_sync(self.channel_layer.group_send)(GLOBAL_STATUS_GROUP, voice_update_event)
        self.accept()

    def disconnect(self, close_code):
        if self.username in ACTIVE_VOICE_USERS.get(self.room_name, set()):
            ACTIVE_VOICE_USERS[self.room_name].discard(self.username)
            if not ACTIVE_VOICE_USERS[self.room_name]:
                del ACTIVE_VOICE_USERS[self.room_name]
        voice_update_event = {'type': 'voice_state_update', 'room_name': self.room_name, 'users': list(ACTIVE_VOICE_USERS.get(self.room_name, set())), 'current_user': self.username, 'action': 'leave'}
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, voice_update_event)
        async_to_sync(self.channel_layer.group_send)(GLOBAL_STATUS_GROUP, voice_update_event)
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        
    def voice_state_update(self, event):
        self.send(text_data=json.dumps(event))
    
    def receive(self, text_data):
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'voice_signal', 'signal_data': json.loads(text_data), 'sender_channel_name': self.channel_name})
    
    def voice_signal(self, event):
        if event['sender_channel_name'] != self.channel_name:
            self.send(text_data=json.dumps(event['signal_data']))

# ===================================================================
# 3. GLOBAL STATUS CONSUMER (Değişiklik yok)
# ===================================================================

class GlobalStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = GLOBAL_STATUS_GROUP
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        initial_status = {'type': 'voice_state_update', 'initial_load': True, 'rooms': {room_name: list(users) for room_name, users in ACTIVE_VOICE_USERS.items()}}
        self.send(text_data=json.dumps(initial_status))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def voice_state_update(self, event):
        self.send(text_data=json.dumps(event))

    def receive(self, text_data): pass
    def chat_message(self, event): pass