import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_notes.settings')

app = Celery('ai_notes')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
