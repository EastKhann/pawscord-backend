from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/voice/(?P<room_name>\w+)/$', consumers.VoiceConsumer.as_asgi()),
    
    # YENİ: Global Durum Bağlantısı
    re_path(r'ws/status/$', consumers.GlobalStatusConsumer.as_asgi()),
]