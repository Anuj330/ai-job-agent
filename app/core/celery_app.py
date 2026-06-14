from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.db import models  # noqa: F401  # register every model before mappers configure

celery_app = Celery(
    "ai_job_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.modules.automation.tasks",
        "app.modules.ai.tasks",
        "app.modules.scrapers.tasks",
    ],
)
celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)
celery_app.conf.beat_schedule = {
    "scheduled-scraping": {
        "task": "app.modules.automation.tasks.run_scheduled_scraping",
        "schedule": crontab(
            hour=settings.scheduled_scrape_hour, minute=settings.scheduled_scrape_minute
        ),
        "kwargs": {
            "keywords": settings.scheduled_scrape_keywords,
            "location": settings.scheduled_scrape_location,
            "max_jobs": settings.scheduled_scrape_max_jobs,
            "sources": settings.scheduled_scrape_sources,
        },
    }
}
