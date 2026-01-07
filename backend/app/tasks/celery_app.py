"""
Celery application configuration.
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "info_hunter",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.ingestion']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'ingest-github-daily': {
        'task': 'app.tasks.ingestion.ingest_github',
        'schedule': 86400.0,  # Daily
        'kwargs': {'topics': ['python', 'javascript', 'react'], 'max_repos': 50}
    },
    'ingest-stackexchange-daily': {
        'task': 'app.tasks.ingestion.ingest_stackexchange',
        'schedule': 86400.0,  # Daily
        'kwargs': {'tags': ['python', 'javascript', 'react', 'nodejs'], 'max_items': 50}
    },
    'ingest-rss-daily': {
        'task': 'app.tasks.ingestion.ingest_rss',
        'schedule': 3600.0,  # Hourly (RSS feeds update more frequently)
        'kwargs': {'max_items_per_feed': 20}
    },
    'run-saved-search-alerts': {
        'task': 'app.tasks.ingestion.run_saved_search_alerts',
        'schedule': 86400.0,  # Daily
    },
}

