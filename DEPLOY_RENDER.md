# Деплой на Render.com

## Что уже готово в проекте
- `settings.py` — автоматически переключается на PostgreSQL через `DATABASE_URL`
- `build.sh` — скрипт сборки (pip install + collectstatic + migrate)
- `render.yaml` — конфиг для автодеплоя
- `whitenoise` — раздача статики без nginx

---

## Шаг 1 — Залить код на GitHub

Если ещё не сделано:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

> Убедитесь, что `.gitignore` включает `.env` и `db.sqlite3` (уже есть).

---

## Шаг 2 — Зарегистрироваться на Render

1. Перейти на [render.com](https://render.com)
2. Нажать **Get Started** → войти через GitHub

---

## Шаг 3 — Создать PostgreSQL базу данных

1. В дашборде нажать **New → PostgreSQL**
2. Настройки:
   - **Name**: `rentcar-db`
   - **Plan**: Free
3. Нажать **Create Database**
4. Скопировать **Internal Database URL** — понадобится на следующем шаге

---

## Шаг 4 — Создать Web Service

1. **New → Web Service**
2. Подключить репозиторий с GitHub
3. Настройки:
   | Поле | Значение |
   |------|----------|
   | Name | `rentcar-web` |
   | Runtime | Python 3 |
   | Build Command | `./build.sh` |
   | Start Command | `gunicorn rentcar.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
   | Plan | Free |

---

## Шаг 5 — Переменные окружения

В разделе **Environment** добавить:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Длинная случайная строка (можно сгенерировать на [djecrety.ir](https://djecrety.ir)) |
| `DEBUG` | `False` |
| `DATABASE_URL` | Internal Database URL из Шага 3 |
| `LOG_LEVEL` | `INFO` |

---

## Шаг 6 — Деплой

Нажать **Create Web Service** — Render автоматически:
1. Установит зависимости (`pip install -r requirements.txt`)
2. Соберёт статику (`collectstatic`)
3. Применит миграции (`migrate`)
4. Запустит gunicorn

Сайт будет доступен по адресу: `https://rentcar-web.onrender.com`

---

## Локальная разработка (без изменений)

Без переменной `DATABASE_URL` проект использует SQLite:

```bash
python manage.py runserver
```

---

## Важные замечания

- **Free план** на Render: сервис засыпает после 15 минут неактивности, первый запрос после сна занимает ~30 секунд.
- **Медиафайлы** (загружаемые изображения) на Free плане не сохраняются между деплоями — диск не персистентный. Для продакшена использовать Cloudinary или AWS S3.
- **Автодеплой**: Render автоматически деплоит при каждом `git push` в основную ветку.
