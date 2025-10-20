from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
from django.core.serializers.json import DjangoJSONEncoder

# --- 1. Oda ViewSet'i ---
# Odaları listelemek için (Sadece okuma izni veriyoruz)
class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]


# --- 2. Mesaj ViewSet'i (Geçmişi Çekme) ---
class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    # Tüm mesajları başlangıçta çek, ancak filtreleme action içinde yapılacak
    queryset = Message.objects.all().order_by('timestamp')
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]

    # /api/messages/history/oda_adi/ şeklinde bir adres tanımlıyoruz
    @action(detail=False, url_path='history/(?P<room_slug>[^/.]+)', methods=['GET'])
    def history(self, request, room_slug=None):
        # Room__slug__exact ile oda adına göre filtrele
        queryset = self.get_queryset().filter(room__slug__exact=room_slug)[:50]

        # Veritabanında eşleşen oda yoksa 404 döndürülmelidir (ancak şimdilik sadece boş liste dönelim)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)