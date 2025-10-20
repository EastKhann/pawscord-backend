"""
Django settings for core project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# GÜVENLİK VE ORTAM AYARLARI (EN ÖNEMLİ KISIM)
# =========================================================

# SECRET_KEY'i doğrudan koda yazmak güvensizdir. Render'dan almasını sağlıyoruz.
# Eğer Render'da tanımlı değilse, yerel geliştirme için eski anahtarı kullanır.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-a_n55upuxdrj-jqri-r0do+o2as=y3um_=364u0-2-9bs25&@v')

# DEBUG modu canlı ortamda kesinlikle False olmalıdır.
# Render'da otomatik olarak 'False' olur, kendi bilgisayarınızda 'True' olur.
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# =========================================================
# HOST VE CORS AYARLARI (BAĞLANTI İZİNLERİ)
# =========================================================

# İzin verilen adresler listesi
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

# Render, kendi canlı adresini bu değişkene yazar. Onu da listeye ekliyoruz.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Frontend'den (Vercel, localhost, ngrok) gelen bağlantı isteklerine izin veriyoruz.
# BU LİSTEDEKİ HER ADRESİN BAŞINDA https:// VEYA http:// OLMALIDIR!
CORS_ALLOWED_ORIGINS = [
    "https://pawscord-frontend.vercel.app",  # Vercel'deki canlı frontend adresi
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://pseudostudiously-reflexional-clara.ngrok-free.dev", # ngrok adresin
]

# WebSocket bağlantılarının güvenli (HTTPS) olarak kurulabilmesi için bu adresleri tanımamız gerekir.
CSRF_TRUSTED_ORIGINS = [
    "https://pawscord-frontend.vercel.app",
    "https://pseudostudiously-reflexional-clara.ngrok-free.dev",
]

# Ngrok gibi proxy'ler üzerinden HTTPS bağlantısı geldiğini Django'ya söyler.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =========================================================
# UYGULAMA TANIMLAMALARI
# =========================================================

INSTALLED_APPS = [
    'daphne', # Channels'ı çalıştırmak için en başa ekliyoruz.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Üçüncü Parti Uygulamalar
    'channels',
    'corsheaders',
    'rest_framework',
    
    # Kendi Uygulamalarımız
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Statik dosyalar için en üste yakın olmalı
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Corsheaders middleware'i
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================================================
# WEBSOCKET (ASGI) AYARLARI
# =========================================================

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# =========================================================
# VERİTABANI AYARLARI
# =========================================================

# Render, veritabanı bilgilerini 'DATABASE_URL' ortam değişkeniyle verir.
# Eğer bu değişken yoksa (kendi bilgisayarımızda), sqlite veritabanını kullanır.
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# =========================================================
# ŞİFRE DOĞRULAMA (PASSWORD VALIDATION)
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =========================================================
# DİĞER AYARLAR
# =========================================================

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =========================================================
# STATİK DOSYA AYARLARI (CANLI ORTAM İÇİN)
# =========================================================

STATIC_URL = 'static/'

# Frontend ayrı bir sunucuda olduğu için STATICFILES_DIRS'e ihtiyacımız yok.
# Bu ayarlar sadece Django'nun kendi dosyaları (admin paneli gibi) içindir.
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'