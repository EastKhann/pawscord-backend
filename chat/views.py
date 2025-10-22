# chat/views.py (OKUNDU OLARAK İŞARETLEME FONKSİYONU EKLENDİ)

from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import json
import os
from django.conf import settings
from django.utils import timezone
from datetime import timezone as dt_timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Message, Room, Conversation, UserProfile, UserChatStatus
from .serializers import MessageSerializer, RoomSerializer, ConversationSerializer, UserProfileSerializer

ADMIN_USER = "Doğukan"


@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request, room_name):
    try:
        data = json.loads(request.body)
        if data.get('username') != ADMIN_USER: return JsonResponse({'error': 'Yetkiniz yok.'}, status=403)
        room = Room.objects.get(slug=room_name)
        deleted_count, _ = Message.objects.filter(room=room).delete()
        print(f"[YÖNETİCİ İŞLEMİ] Sohbet temizlendi. Oda: '{room_name}', Silinen Mesaj Sayısı: {deleted_count}")
        return JsonResponse({'status': 'ok', 'deleted_count': deleted_count})
    except Room.DoesNotExist: return JsonResponse({'error': 'Oda bulunamadı.'}, status=404)
    except Exception as e: return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_all_rooms(request):
    try:
        all_rooms = list(Room.objects.values('slug', 'channel_type').order_by('slug'))
        general_room = next((r for r in all_rooms if r['slug'] == 'genel'), None)
        other_rooms = sorted([r for r in all_rooms if r['slug'] != 'genel'], key=lambda x: x['slug'])
        sorted_rooms = [general_room] + other_rooms if general_room else other_rooms
        return JsonResponse(sorted_rooms, safe=False)
    except Exception as e:
        print(f"[API KRİTİK HATA] Oda listesi çekilirken hata oluştu: {e}")
        return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_all_users(request):
    all_users = UserProfile.objects.all().order_by('username')
    serializer = UserProfileSerializer(all_users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_profile(request, username):
    try:
        user_profile = UserProfile.objects.get(username=username)
        serializer = UserProfileSerializer(user_profile, context={'request': request})
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Kullanıcı bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def update_user_profile(request):
    username = request.data.get('username')
    if not username:
        return Response({'error': 'Kullanıcı adı gerekli.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_profile = UserProfile.objects.get(username=username)
        
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'global_user_status',
                {
                    'type': 'user_profile_update_handler',
                    'user_data': serializer.data
                }
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Kullanıcı bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)


class MessageHistoryView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        room_name = self.kwargs.get('room_name')
        if room_name:
            try:
                room = Room.objects.get(slug=room_name)
                return Message.objects.filter(room=room).select_related('reply_to').prefetch_related('reactions').order_by('-timestamp')[:50][::-1]
            except Room.DoesNotExist: return Message.objects.none()
        conversation_id = self.kwargs.get('conversation_id')
        if conversation_id:
            try:
                conv = Conversation.objects.get(id=conversation_id)
                return Message.objects.filter(conversation=conv).select_related('reply_to').prefetch_related('reactions').order_by('-timestamp')[:50][::-1]
            except Conversation.DoesNotExist: return Message.objects.none()
        return Message.objects.none()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_conversations(request):
    username = request.query_params.get('username')
    if not username: return Response({'error': 'Kullanıcı adı gerekli.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_profile = UserProfile.objects.get(username=username)
        conversations = user_profile.conversations.all().prefetch_related('participants')
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data)
    except UserProfile.DoesNotExist: return Response({'error': 'Kullanıcı bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_or_create_conversation(request):
    user1_username, user2_username = request.data.get('user1'), request.data.get('user2')
    if not user1_username or not user2_username: return Response({'error': 'İki kullanıcı adı da gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user1, user2 = UserProfile.objects.get(username=user1_username), UserProfile.objects.get(username=user2_username)
        conversation = Conversation.objects.annotate(num_participants=Count('participants')).filter(participants=user1).filter(participants=user2).filter(num_participants=2).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(user1, user2)
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data)
    except UserProfile.DoesNotExist: return Response({'error': 'Kullanıcılardan biri bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def upload_image(request):
    image_file, username, room_slug, conversation_id, content, reply_to_id = (
        request.FILES.get('image'), request.data.get('username'), request.data.get('room_slug'),
        request.data.get('conversation_id'), request.data.get('content', ''), request.data.get('reply_to')
    )
    if not image_file or not username or (not room_slug and not conversation_id): 
        return Response({'error': 'Eksik bilgi.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room, conversation = None, None
        target_group_name = None
        if room_slug: 
            room = Room.objects.get(slug=room_slug)
            target_group_name = f'chat_{room.slug}'
        elif conversation_id: 
            conversation = Conversation.objects.get(id=conversation_id)
            target_group_name = f'dm_{conversation.id}'
        
        # chat/consumers.py içindeki create_message_and_get_data'e referans
        from .consumers import create_message_and_get_data
        
        message_data = create_message_and_get_data(
            target_model_instance=room or conversation,
            username=username, 
            image_file=image_file, 
            content=content or None,
            reply_to_id=reply_to_id
        )

        channel_layer = get_channel_layer()
        event_type = 'chat_message_handler' if room else 'dm_message_handler'
        
        if message_data.get('image'):
             message_data['image_url'] = request.build_absolute_uri(message_data['image'])
        
        async_to_sync(channel_layer.group_send)(target_group_name, {'type': event_type, **message_data})
        print(f"[ANONS GÖNDERİLDİ - Resim] Grup: {target_group_name}")

        notification_data = {k:v for k,v in message_data.items() if k not in ['image']}
        notification_data['content'] = "[Resim]"
        async_to_sync(channel_layer.group_send)(
            'global_voice_status', 
            {
                'type': 'global_message_notification', 
                **notification_data, 
                'room_slug': room_slug, 
                'conversation_id': conversation_id
            }
        )
        
        return Response(message_data, status=status.HTTP_201_CREATED)
        
    except (Room.DoesNotExist, Conversation.DoesNotExist): return Response({'error': 'Hedef sohbet bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e: return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_default_avatars(request):
    try:
        avatar_dir = os.path.join(settings.BASE_DIR, 'frontend', 'public', 'avatars')
        if not os.path.isdir(avatar_dir):
            return Response([], status=status.HTTP_200_OK)
        image_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.gif']
        filenames = [f for f in os.listdir(avatar_dir) if os.path.splitext(f)[1].lower() in image_extensions]
        urls = [f'/avatars/{filename}' for filename in filenames]
        return Response(urls)
    except Exception as e:
        print(f"[HATA] Varsayılan avatarlar listelenemedi: {e}")
        return Response({'error': 'Avatarlar alınamadı.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mark_chat_as_read(request):
    username = request.data.get('username')
    room_slug = request.data.get('room_slug')
    conversation_id = request.data.get('conversation_id')

    if not username or (not room_slug and not conversation_id):
        return Response({'error': 'Eksik bilgi.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = UserProfile.objects.get(username=username)
        if room_slug:
            room = Room.objects.get(slug=room_slug)
            UserChatStatus.objects.update_or_create(
                user=user, room=room, conversation=None,
                defaults={'last_read_timestamp': timezone.now()}
            )
        elif conversation_id:
            conversation = Conversation.objects.get(id=conversation_id)
            UserChatStatus.objects.update_or_create(
                user=user, room=None, conversation=conversation,
                defaults={'last_read_timestamp': timezone.now()}
            )
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    except (UserProfile.DoesNotExist, Room.DoesNotExist, Conversation.DoesNotExist):
        return Response({'error': 'Kullanıcı veya sohbet bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)