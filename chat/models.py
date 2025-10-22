# chat/models.py (REAKSİYON, YANITLAMA VE OKUNDU BİLGİSİ EKLENDİ)

from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    ip_address = models.CharField(max_length=45, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    status_message = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return self.username

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    CHANNEL_TYPE_CHOICES = [('text', 'Metin'), ('voice', 'Sesli')]
    channel_type = models.CharField(max_length=5, choices=CHANNEL_TYPE_CHOICES, default='text')

    def __str__(self):
        return self.slug

class Conversation(models.Model):
    participants = models.ManyToManyField(UserProfile, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        usernames = " & ".join([user.username for user in self.participants.all()])
        return f"Konuşma: {usernames}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    username = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_edited = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        target = self.room.slug if self.room else f"DM ({self.conversation_id})"
        has_image = " [Resim]" if self.image else ""
        reply_info = f" (yanıt: {self.reply_to.id})" if self.reply_to else ""
        return f"{self.username} -> {target}{reply_info}: {self.content or ''}{has_image}"

class Reaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    username = models.CharField(max_length=255)
    emoji = models.CharField(max_length=50)

    class Meta:
        unique_together = ('message', 'username', 'emoji')

    def __str__(self):
        return f"'{self.username}' -> '{self.message.id}' için '{self.emoji}' tepkisi"

class UserChatStatus(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    last_read_timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'room', 'conversation')

    def __str__(self):
        target = self.room.slug if self.room else f"DM({self.conversation.id})"
        return f"{self.user.username} - {target} - {self.last_read_timestamp}"
