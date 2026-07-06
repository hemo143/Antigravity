#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Auto-create the admin user on first deploy (only if the DJANGO_SUPERUSER_*
# env vars are set and the user doesn't already exist). Safe to run every deploy.
python manage.py createsuperuser --no-input 2>/dev/null || echo "superuser step skipped (already exists or env vars not set)"
