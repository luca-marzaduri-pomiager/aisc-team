"""Presentation bootstrap: migrate a fresh database before serving requests."""
import os
import subprocess
import sys

sys.path.insert(0, '/app')
subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
user, created = get_user_model().objects.get_or_create(username='demo-admin', defaults={'email': 'admin@example.invalid'})
if created:
    user.is_superuser = user.is_staff = True
    user.set_password(os.environ['DEMO_ADMIN_PASSWORD'])
    user.save()
os.execvp('uvicorn', ['uvicorn', 'config.asgi:application', '--host', '0.0.0.0', '--port', '8000', '--no-access-log'])
