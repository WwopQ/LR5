"""
Django settings for rentcar project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ─── Пути ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env из корня проекта
load_dotenv(BASE_DIR / '.env')

# ─── Безопасность ────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-insecure-key-change-in-env')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

# ─── Приложения ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Наши приложения — бизнес-логика
    'car_rental',
    'users',

    # Наши приложения — контентные страницы
    'pages',
    'news',
    'faq',
    'vacancies',
    'reviews',
    'promos',
]

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rentcar.urls'

# ─── Шаблоны ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Глобальная папка templates/ в корне проекта
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Тайм-зона, дата, текстовый календарь
                'rentcar.context_processors.datetime_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'rentcar.wsgi.application'

# ─── База данных ─────────────────────────────────────────────────────────────
# Локально — SQLite; на Render/Docker — PostgreSQL через DATABASE_URL
_DATABASE_URL = os.getenv('DATABASE_URL')
if _DATABASE_URL:
    import dj_database_url          # pip install dj-database-url
    DATABASES = {'default': dj_database_url.config(default=_DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── Аутентификация ──────────────────────────────────────────────────────────
# Используем стандартного User из Django.
# Профиль клиента — отдельная модель Client (OneToOne → User) в app car_rental.
# Если понадобится кастомный User — раскомментировать и создать модель:
# AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ─── Локализация ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Minsk'   # Беларусь UTC+3
USE_I18N = True
USE_TZ = True                # Хранить даты в UTC, отображать в TIME_ZONE

# ─── Статика ─────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'

# Папка со статикой, общей для всего проекта (не приложений)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Куда собирается статика командой collectstatic (для продакшена)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ─── Медиафайлы (загружаемые пользователями) ─────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Первичный ключ по умолчанию ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Логирование ─────────────────────────────────────────────────────────────
# Уровень берётся из .env: LOG_LEVEL=DEBUG | INFO | WARNING | ERROR
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
            'datefmt': '%d/%m/%Y %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        # Вывод в консоль PyCharm
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # Запись в файл
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        # Логгеры для каждого приложения
        'car_rental': {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'users':      {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'pages':      {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'news':       {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'faq':        {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'vacancies':  {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'reviews':    {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
        'promos':     {'handlers': ['console', 'file'], 'level': LOG_LEVEL, 'propagate': False},
    },
}
