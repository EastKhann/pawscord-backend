from django.db import models
from django.utils import timezone  # Zaman damgası için
from django.db import models

# 1. Oda Modeli (Oda adları kalıcı olmalı)
class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, default='genel')  # URL için kısa isim

    def __str__(self):
        return self.name


# 2. Mesaj Modeli (Mesajları kalıcı olarak saklamak için)
class Message(models.Model):
    # Foreign Key ile hangi odaya ait olduğunu belirtiyoruz
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    username = models.CharField(max_length=255)
    content = models.TextField()

    # Otomatik olarak atılma zamanını kaydet
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']  # Eskiden yeniye doğru sırala

    def __str__(self):
        return f'{self.username} - {self.timestamp.strftime("%H:%M")}'
class UserProfile(models.Model):
    # Kullanıcının ağdaki dış IP adresini saklar
    ip_address = models.CharField(max_length=45, unique=True, null=True, blank=True) 
    username = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username