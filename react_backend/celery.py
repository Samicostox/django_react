from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings  # Ensure this is the correct import for your settings module

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'react_backend.settings')

app = Celery('react_backend')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Explicitly set the broker URL from Django settings
app.conf.broker_url = settings.CELERY_BROKER_URL

# Set broker_connection_retry_on_startup to True to retain retrying connections on startup behavior
app.conf.broker_connection_retry_on_startup = True

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
