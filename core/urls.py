# core/urls.py (TÜM DOSYA YOLLARI İÇİN NİHAİ DÜZELTME)

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Django Admin Paneli
    path('admin/', admin.site.urls),

    # API yolları
    path('api/', include('chat.urls')), 
] 

# DEBUG modunda medya dosyalarının (/media/) sunulmasını sağlar.
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]

# Statik dosyalar Whitenoise tarafından yönetilir, bu satır geliştirme sunucusu için kalabilir.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# KRİTİK: React uygulamasını ve public klasöründeki dosyaları sunma
# Bu bloğun her zaman en sonda olduğundan emin ol!
urlpatterns += [
    # Ana sayfa isteğini doğrudan index.html'e yönlendir
    re_path(r'^$', TemplateView.as_view(template_name='index.html')),
    
    # API, MEDYA, STATİK veya AVATARS ile başlamayan TÜM diğer istekleri index.html'e yönlendir.
    re_path(r'^(?!api/|media/|static/|avatars/|sounds/).*$', TemplateView.as_view(template_name='index.html')),
]
