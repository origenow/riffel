#!/usr/bin/env bash
# Script de build para Render
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
