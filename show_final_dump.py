import os
import sys

# Windows terminalindeki kodlama sorunlarını çözmek için
# Çıktı dosyalarının bu script'i çalıştırdığın yerde oluşacağını unutma.
sys.stdout = open('project_dump_output.txt', 'w', encoding='utf-8')
sys.stderr = open('project_dump_errors.txt', 'w', encoding='utf-8')


def print_file_content(base_path, filepath):
    # Script'in, listenin içindeki tam yolu (fpath) kullanmasını sağlıyoruz,
    # base_path'i (şimdilik) yok sayıyoruz çünkü listeniz zaten tam yolları içeriyor.
    full_path = filepath

    print("\n" + "=" * 60)
    print(f"DOSYA: [{filepath.upper()}] BAŞLANGIÇ")
    print("=" * 60)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                print(f"{i:03d}: {line}")
    except FileNotFoundError:
        print(f"HATA: DOSYA BULUNAMADI: {full_path}")
    except Exception as e:
        print(f"HATA: OKUMA HATASI {full_path}: {e}")

    print("=" * 60)
    print(f"DOSYA: [{filepath.upper()}] SON")
    print("=" * 60 + "\n")


def generate_project_dump():
    # Proje yolu buraya manuel olarak girilmelidir (Sizin yolunuz)
    project_path = r"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT"

    if not os.path.isdir(project_path):
        print(f"\nHATA: '{project_path}' geçerli bir dizin yolu değil.")
        sys.exit(1)

    # === GÜNCELLENMİŞ DOSYA LİSTESİ ===
    files_to_check = [
        # === DJANGO BACKEND ===
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\core\asgi.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\core\settings.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\core\urls.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\core\wsgi.py",

        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\consumers.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\models.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\views.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\routing.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\urls.py",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\serializers.py",  # YENİ EKLENDİ
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\__init__.py",

        # === FRONTEND (React) ===
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\App.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\index.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\RoomList.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\ChatUserList.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\VoiceUserList.js",

        # YENİ EKLENEN FRONTEND DOSYALARI
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\ImageModal.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\Message.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\MessageEditForm.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\ReactionPicker.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\ReplyPreview.js",
        rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\UserProfilePanel.js",

        # KULLANILMAYAN (404 VERECEK) ESKİ DOSYALAR - YORUMA ALINDI
        # rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\chat\consumer.py",
        # rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\Room.js",
        # rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\components\MessageInput.js",
        # rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\components\MessageList.js",
        # rf"C:\Users\Eastkhan\Software\JavaScript\PAWSCORD_CHAT\frontend\src\components\UserList.js",
    ]
    # === LİSTE SONU ===

    print("\n" + "#" * 70)
    print(f"PROJE KAYNAK KODU DÖKÜMÜ - DİZİN: {project_path}")
    print("#" * 70 + "\n")

    for fpath in files_to_check:
        # base_path'i (project_path) kullanmıyoruz çünkü fpath zaten tam yolu içeriyor
        print_file_content(None, fpath)


if __name__ == "__main__":
    generate_project_dump()
