from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Yeni viewset'leri import edin
from .views import RoomViewSet, MessageViewSet
from . import consumers  # (Gerekirse)

router = DefaultRouter()
# Odaları listeleyecek API (ileride kullanırız)
router.register(r'rooms', RoomViewSet, basename='room')
# Mesaj API'sini dahil et
router.register(r'messages', MessageViewSet, basename='message')

websocket_urlpatterns = [
    # ... (mevcut websocket yönlendirmesi) ...
]

# HTTP URL'lerini burada tanımlıyoruz
urlpatterns = [
    # API endpoint'lerini /api/ altında birleştir
    path('', include(router.urls)),

    # WebSocket URL'leri (bu dosyanın en altında zaten var, ama düzenleme yapmak gerekebilir)
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]