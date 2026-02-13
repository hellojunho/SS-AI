import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ss_ai_drf.settings")

app = Celery("ss_ai_drf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
