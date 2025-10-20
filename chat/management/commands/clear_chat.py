# chat/management/commands/clear_chat.py (GÜNCELLENMİŞ HALİ)

from django.core.management.base import BaseCommand
from chat.models import Message

class Command(BaseCommand):
    help = 'Deletes all messages from the chat history'

    # Sunucuda "yes" yazamayacağımız için '--no-input' seçeneği ekliyoruz
    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not ask for confirmation before deleting.',
        )

    def handle(self, *args, **kwargs):
        message_count = Message.objects.count()

        if message_count == 0:
            self.stdout.write(self.style.WARNING('Chat history is already empty.'))
            return

        # Eğer --no-input bayrağı kullanılmadıysa, onay iste
        if not kwargs['no_input']:
            self.stdout.write(self.style.WARNING(f'This will permanently delete {message_count} messages.'))
            confirmation = input('Are you sure you want to continue? (yes/no): ')
            if confirmation.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Tüm mesajları sil
        Message.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {message_count} messages.'))