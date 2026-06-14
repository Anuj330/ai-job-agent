import asyncio
import logging

from app.core.celery_app import celery_app
from app.modules.scrapers.bayt import scrape_and_save_bayt_jobs
from app.modules.scrapers.indeed import scrape_and_save_indeed_jobs
from app.modules.scrapers.linkedin import scrape_and_save_linkedin_jobs
from app.modules.scrapers.naukri import scrape_and_save_naukri_jobs

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def scrape_jobs(self, source: str, url: str) -> dict[str, str]:
    """Provider adapters should replace this task body while preserving its queue contract."""
    logger.info(
        "scrape_requested",
        extra={"source": source, "url": url, "task_id": self.request.id},
    )
    return {"source": source, "url": url, "status": "accepted"}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def scrape_linkedin_jobs(
    self, keywords: str, location: str, max_jobs: int = 25
) -> dict[str, str | int]:
    saved = asyncio.run(scrape_and_save_linkedin_jobs(keywords, location, max_jobs))
    logger.info(
        "linkedin_scrape_completed",
        extra={
            "keywords": keywords,
            "location": location,
            "saved": saved,
            "task_id": self.request.id,
        },
    )
    return {"source": "linkedin", "status": "completed", "saved": saved}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def scrape_naukri_jobs(
    self, keywords: str, location: str, max_jobs: int = 25
) -> dict[str, str | int]:
    saved = asyncio.run(scrape_and_save_naukri_jobs(keywords, location, max_jobs))
    logger.info(
        "naukri_scrape_completed",
        extra={
            "keywords": keywords,
            "location": location,
            "saved": saved,
            "task_id": self.request.id,
        },
    )
    return {"source": "naukri", "status": "completed", "saved": saved}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def scrape_bayt_jobs(
    self, keywords: str, location: str, max_jobs: int = 25
) -> dict[str, str | int]:
    saved = asyncio.run(scrape_and_save_bayt_jobs(keywords, location, max_jobs))
    logger.info(
        "bayt_scrape_completed",
        extra={
            "keywords": keywords,
            "location": location,
            "saved": saved,
            "task_id": self.request.id,
        },
    )
    return {"source": "bayt", "status": "completed", "saved": saved}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def scrape_indeed_jobs(
    self, keywords: str, location: str, max_jobs: int = 25
) -> dict[str, str | int]:
    saved = asyncio.run(scrape_and_save_indeed_jobs(keywords, location, max_jobs))
    logger.info(
        "indeed_scrape_completed",
        extra={
            "keywords": keywords,
            "location": location,
            "saved": saved,
            "task_id": self.request.id,
        },
    )
    return {"source": "indeed", "status": "completed", "saved": saved}
