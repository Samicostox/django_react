from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

from react_backend import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_backend.settings')

app = Celery('react_backend')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.autodiscover_tasks()