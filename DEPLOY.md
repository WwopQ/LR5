# Деплой RentCar на Render.com

## Подготовка: что нужно сделать один раз

### 1. Зарегистрируйся на Render.com
Перейди на https://render.com → Sign Up (через GitHub).

### 2. Залей проект на GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ТВО_ИМЯ/rentcar.git
git push -u origin main
```

> **Важно:** `.env` должен быть в `.gitignore` — секреты не пушим!

---

## Деплой шаг за шагом

### Шаг 1. Создай PostgreSQL базу данных

1. Render Dashboard → **New** → **PostgreSQL**
2. Заполни:
   - **Name:** `rentcar-db`
   - **Region:** Frankfurt (EU)
   - **Plan:** Free
3. Нажми **Create Database**
4. Дождись статуса **Available**
5. Скопируй **Internal Database URL** (пригодится на шаге 3)

---

### Шаг 2. Создай Web Service

1. Render Dashboard → **New** → **Web Service**
2. Подключи репозиторий GitHub
3. Заполни настройки:

| Поле | Значение |
|------|----------|
| **Name** | `rentcar` |
| **Region** | Frankfurt (EU) |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn rentcar.wsgi:application --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

---

### Шаг 3. Добавь переменные окружения

В разделе **Environment** добавь переменные:

| Ключ | Значение |
|------|----------|
| `SECRET_KEY` | Длинная случайная строка (генери на https://djecrety.ir/) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `rentcar.onrender.com` |
| `DATABASE_URL` | Internal Database URL из шага 1 |
| `LOG_LEVEL` | `WARNING` |

---

### Шаг 4. Настрой статику (WhiteNoise)

Добавь в `rentcar/settings.py` (уже должно быть):
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← после SecurityMiddleware
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

### Шаг 5. Добавь миграции в Build Command

Обнови **Build Command** в настройках Render:
```
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

---

### Шаг 6. Создай суперпользователя

После успешного деплоя зайди в Render Dashboard →
**Web Service** → **Shell** и выполни:
```bash
python manage.py createsuperuser
```

---

## Локальный запуск через Docker

```bash
# 1. Скопируй .env.example → .env и заполни
cp .env.example .env

# 2. Собери и запусти контейнеры
docker-compose up --build

# 3. В другом терминале создай суперпользователя
docker-compose exec web python manage.py createsuperuser

# 4. Открой браузер
# http://localhost:8000
# http://localhost:8000/admin
```

### Остановка
```bash
docker-compose down          # остановить
docker-compose down -v       # остановить + удалить данные БД
```

---

## Запуск тестов

```bash
# Локально (с djvenv активированным)
pip install pytest pytest-django pytest-cov
pytest

# С отчётом о покрытии в браузере
pytest --cov-report=html
start htmlcov/index.html     # Windows
```

---

## Структура проекта

```
rentcar/
├── manage.py
├── pytest.ini
├── conftest.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                 ← не в git!
├── .env.example
├── DEPLOY.md
├── rentcar/             ← настройки Django
│   ├── settings.py
│   └── urls.py
├── pages/               ← Главная, О компании, Контакты, Политика
├── news/                ← Новости
├── faq/                 ← Вопросы и ответы
├── vacancies/           ← Вакансии
├── reviews/             ← Отзывы
├── promos/              ← Промокоды
├── users/               ← Аутентификация, Profile
├── car_rental/          ← Основная бизнес-логика
├── templates/           ← base.html
├── static/              ← CSS, JS
├── media/               ← загружаемые файлы (не в git)
└── logs/                ← лог-файлы (не в git)
```
