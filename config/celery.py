"""Celery application setup."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("hookrelay")
# Read all settings that start with CELERY_ from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Look for a tasks.py file in every installed app.
app.autodiscover_tasks()