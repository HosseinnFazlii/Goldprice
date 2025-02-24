import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # Update 'core' with your project name

app = Celery("core")  # Replace 'core' with your actual project name

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in Django apps
app.autodiscover_tasks()

# Define the Celery schedule for periodic tasks
app.conf.beat_schedule = {
    "fetch-gold-prices-every-hour": {
        "task": "gold.tasks.fetch_and_save_gold_prices",
        "schedule": 60.0,  # Every 1 hour (in seconds)
    },
}
