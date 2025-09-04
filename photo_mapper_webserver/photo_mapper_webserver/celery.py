import os

from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "photo_mapper_webserver.settings")

app = Celery("photo_mapper_webserver")

# Configure celery from Django settings file with its own namespace
app.config_from_object("django.conf.settings", namespace="CELERY")

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
    