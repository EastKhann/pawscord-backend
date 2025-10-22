# chat/serializers.py (REAKSİYON VE YANITLAMA EKLENDİ)

from rest_framework import serializers
from .models import Message, Room, Conversation, UserProfile, Reaction

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['username', 'avatar', 'status_message', 'last_seen']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['name', 'slug', 'channel_type']

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'username', 'emoji']

class RepliedMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'username', 'content']

class MessageSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source='image', read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    reply_to = RepliedMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'conversation', 'username', 
            'content', 'image', 'image_url', 'timestamp', 'is_edited',
            'reactions', 'reply_to'
        ]
        read_only_fields = ['timestamp']

class ConversationParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['username', 'avatar', 'status_message']

class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at']
