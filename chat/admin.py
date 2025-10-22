# chat/admin.py (TAM HALİ)

from django.contrib import admin
from .models import Room, Message, UserProfile, Conversation

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'last_seen')
    search_fields = ('username', 'ip_address')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'channel_type', 'timestamp')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('channel_type',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant_names', 'created_at')
    filter_horizontal = ('participants',) # Kullanıcıları seçmek için daha iyi bir arayüz

    def participant_names(self, obj):
        return " & ".join([user.username for user in obj.participants.all()])
    participant_names.short_description = 'Katılımcılar'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('username', 'room', 'conversation', 'content_summary', 'image_preview', 'timestamp')
    list_filter = ('room', 'conversation', 'timestamp')
    search_fields = ('username', 'content')

    def content_summary(self, obj):
        if obj.content:
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return "[İçerik Yok]"
    content_summary.short_description = 'İçerik Özeti'

    def image_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Yok"
    image_preview.short_description = 'Resim Önizleme'