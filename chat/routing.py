# chat/routing.py (TAM HALİ)

from django.urls import re_path
from . import consumers

global_routing = [
    re_path(r'ws/status/$', consumers.GlobalStatusConsumer.as_asgi()),
]

chat_voice_routing = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/voice/(?P<room_name>\w+)/$', consumers.VoiceConsumer.as_asgi()),
]

dm_routing = [
    re_path(r'ws/dm/(?P<conversation_id>\d+)/$', consumers.DMConsumer.as_asgi()),
]

websocket_urlpatterns = global_routing + chat_voice_routing + dm_routing
