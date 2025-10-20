from rest_framework import serializers
from .models import Room, Message # Message modelini içeri al

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('id', 'name', 'slug')

# YENİ: Mesaj Serializer
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'username', 'content', 'timestamp')