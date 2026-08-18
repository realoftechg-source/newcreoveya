#!/usr/bin/env bash
# Render build script for AI Live Studio
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate
