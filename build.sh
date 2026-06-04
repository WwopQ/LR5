#!/usr/bin/env bash
set -o errexit

mkdir -p logs
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
