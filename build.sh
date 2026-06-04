#!/usr/bin/env bash
set -o errexit

mkdir -p logs
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Загружаем начальные данные (только если таблицы пустые)
python manage.py loaddata \
  car_rental/fixtures/initial_data.json \
  news/fixtures/initial_data.json \
  faq/fixtures/initial_data.json \
  vacancies/fixtures/initial_data.json \
  promos/fixtures/initial_data.json \
  reviews/fixtures/initial_data.json \
  pages/fixtures/initial_data.json \
  || true
