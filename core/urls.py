from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView 
from django.conf import settings
from django.conf.urls.static import static 
import os # Eğer settings'te kullanılıyorsa buraya da ekleyin

# Başlangıçta boş bir URL listesi tanımlıyoruz
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chat.urls')), 
]

# KRİTİK DÜZELTME: DEBUG modunda statik dosyaları EN YÜKSEK ÖNCELİKTE sunuyoruz.
# Bu, tüm diğer kurallardan önce çalışır ve /static/ isteklerini yakalar.
if settings.DEBUG:
    # BASE_DIR'ı tanımlı kabul ediyoruz. (settings.py'den)
    BASE_DIR = settings.BASE_DIR 
    
    # /static/ ile başlayan istekleri frontend/build klasöründen sun
    urlpatterns += static(
        settings.STATIC_URL, 
        document_root=os.path.join(BASE_DIR, 'frontend/build/static')
    )
    
    # Sadece /admin/ ve /api/ olmayan diğer tüm adresleri React'e yönlendiriyoruz
    urlpatterns += [
        re_path(r'^(?:.*)/?$', TemplateView.as_view(template_name='index.html')), 
    ]
else:
    # DEBUG=False ise, sadece API/Admin ve React ana sayfa kuralı kalır
    urlpatterns += [
        re_path(r'^(?:.*)/?$', TemplateView.as_view(template_name='index.html')),
    ]