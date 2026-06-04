"""
URL configuration for rentcar project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Админ-панель
    path('admin/', admin.site.urls),

    # ─── Бизнес-логика ───────────────────────────────────────────────────────
    path('cars/', include('car_rental.urls')),
    path('users/', include('users.urls')),

    # ─── Контентные страницы ─────────────────────────────────────────────────
    path('', include('pages.urls')),           # Главная + О компании + Политика конфид.
    path('news/', include('news.urls')),
    path('faq/', include('faq.urls')),
    path('vacancies/', include('vacancies.urls')),
    path('reviews/', include('reviews.urls')),
    path('promos/', include('promos.urls')),
]

# Раздача медиафайлов в режиме разработки (DEBUG=True)
# В продакшене медиа отдаёт nginx/apache
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Раздача медиафайлов (для хостинга, где нет nginx)
if not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)