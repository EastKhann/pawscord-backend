from django.contrib import admin
from .models import Room, Message, UserProfile # Oluşturduğunuz tüm modelleri import edin

# Mesajları yönetmek için bir sınıf oluşturmak faydalı olur (Opsiyonel)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'username', 'content', 'timestamp')
    list_filter = ('room', 'timestamp')
    search_fields = ('username', 'content')
    ordering = ('-timestamp',)

# Modelleri Admin paneline kaydedin
admin.site.register(Room)
admin.site.register(Message, MessageAdmin) # Mesajları silmek için bu gerekli
admin.site.register(UserProfile)