import os
from django.core.asgi import get_asgi_application
import django # Yeni setup için gerekli

# 1. Ayarları Yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 2. Django'nun Uygulamalarını Yükle ve Başlat (AppRegistryNotReady'yi çözer)
django.setup()

# 3. Gerekli Channels import'ları (Artık güvenli)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat import routing

# Django'nun HTTP uygulamasını al
django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    "http": django_asgi_app, # HTTP istekleri
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns # WebSocket yönlendirmesi
        )
    ),
})