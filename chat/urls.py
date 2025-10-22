# chat/urls.py (OKUNDU OLARAK İŞARETLEME URL'Sİ EKLENDİ)

from django.urls import path
from . import views

urlpatterns = [
    # Mesajlar
    path('messages/history/room/<str:room_name>/', views.MessageHistoryView.as_view(), name='message-history-room'),
    path('messages/history/dm/<int:conversation_id>/', views.MessageHistoryView.as_view(), name='message-history-dm'),
    path('messages/upload_image/', views.upload_image, name='upload-image'),

    # Odalar
    path('rooms/list/', views.get_all_rooms, name='room-list'),
    path('rooms/<str:room_name>/clear/', views.clear_chat, name='clear-chat'),

    # DM
    path('conversations/', views.list_conversations, name='list-conversations'),
    path('conversations/find_or_create/', views.get_or_create_conversation, name='get-or-create-conversation'),

    # Kullanıcılar ve Durumlar
    path('users/list_all/', views.list_all_users, name='list-all-users'),
    path('users/profile/<str:username>/', views.get_user_profile, name='get-user-profile'),
    path('users/update_profile/', views.update_user_profile, name='update-user-profile'),
    path('users/default_avatars/', views.list_default_avatars, name='list-default-avatars'),
    
    # <<< YENİ: Okundu olarak işaretleme için yeni API endpoint'i >>>
    path('chats/mark_as_read/', views.mark_chat_as_read, name='mark-chat-as-read'),
]