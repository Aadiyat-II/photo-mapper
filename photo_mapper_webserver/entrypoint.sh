#!/bin/sh
echo "Migrating models...";
conda run --no-capture-output -n photo-mapping-env python manage.py migrate --noinput;

DJANGO_SCRIPT="
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')

if not User.objects.filter(username=username).exists():
    print('Creating new superuser...')
    User.objects.create_superuser(
        username=username,
        password=password,
        email=email
    )
else:
    print('Superuser already exists. Skipping...')
"

echo "Creating superuser...";
echo "$DJANGO_SCRIPT" | conda run --no-capture-output -n photo-mapping-env python manage.py shell;

echo "Starting dev server...";
conda run --no-capture-output -n photo-mapping-env python manage.py runserver 0.0.0.0:8000;