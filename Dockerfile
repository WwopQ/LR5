# ─── Стадия сборки ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Системные зависимости для psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ─── Финальный образ ─────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости из builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Системные библиотеки для psycopg2 runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем код проекта
COPY . .

# Создаём папки для статики, медиа и логов
RUN mkdir -p staticfiles media logs

# Собираем статику
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Запуск через gunicorn
CMD ["gunicorn", "rentcar.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
