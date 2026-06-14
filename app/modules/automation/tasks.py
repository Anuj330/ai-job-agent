from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Any, cast

from app.core.celery_app import celery_app
from app.core.config import settings
from app.modules.ai.cover_letter_generation import (
    CoverLetterGenerationRequest,
    CoverLetterGenerationResult,
    CoverLetterTone,
    get_cover_letter_generation_service,
)
from app.modules.ai.matching import MatchAnalysisRequest, get_matching_service
from app.modules.scrapers.tasks import (
    scrape_bayt_jobs,
    scrape_indeed_jobs,
    scrape_linkedin_jobs,
    scrape_naukri_jobs,
)

logger = logging.getLogger(__name__)


def _normalized_sources(sources: list[str] | None) -> list[str]:
    configured_sources = sources or settings.scheduled_scrape_sources
    normalized = [source.strip().lower() for source in configured_sources if source.strip()]
    if not normalized:
        raise ValueError("At least one scrape source is required")
    return normalized


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_scheduled_scraping(
    self,
    keywords: str | None = None,
    location: str | None = None,
    max_jobs: int | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Queue source scrapers for a scheduled job run."""
    resolved_keywords = keywords or settings.scheduled_scrape_keywords
    resolved_location = location or settings.scheduled_scrape_location
    resolved_max_jobs = max_jobs or settings.scheduled_scrape_max_jobs
    resolved_sources = _normalized_sources(sources)

    task_ids: list[dict[str, str]] = []
    for source in resolved_sources:
        if source == "linkedin":
            task = scrape_linkedin_jobs.delay(
                resolved_keywords, resolved_location, resolved_max_jobs
            )
        elif source == "naukri":
            task = scrape_naukri_jobs.delay(resolved_keywords, resolved_location, resolved_max_jobs)
        elif source == "bayt":
            task = scrape_bayt_jobs.delay(resolved_keywords, resolved_location, resolved_max_jobs)
        elif source == "indeed":
            task = scrape_indeed_jobs.delay(resolved_keywords, resolved_location, resolved_max_jobs)
        else:
            raise ValueError(f"Unsupported scrape source: {source}")
        task_ids.append({"source": source, "task_id": task.id})

    logger.info(
        "scheduled_scraping_queued",
        extra={
            "task_id": self.request.id,
            "keywords": resolved_keywords,
            "location": resolved_location,
            "max_jobs": resolved_max_jobs,
            "sources": resolved_sources,
        },
    )
    return {
        "status": "queued",
        "keywords": resolved_keywords,
        "location": resolved_location,
        "max_jobs": resolved_max_jobs,
        "sources": resolved_sources,
        "tasks": task_ids,
    }


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_ai_analysis(self, resume_text: str, job_description: str) -> dict[str, Any]:
    """Run resume/job fit analysis and return the structured result."""

    async def _run() -> dict[str, Any]:
        service = get_matching_service()
        result = await service.analyze(
            MatchAnalysisRequest(
                resume_text=resume_text,
                job_description=job_description,
            )
        )
        return result.model_dump()

    result = asyncio.run(_run())
    logger.info(
        "ai_analysis_completed",
        extra={"task_id": self.request.id, "match_score": result["match_score"]},
    )
    return result


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_cover_letter(
    self,
    resume_text: str,
    job_description: str,
    tone: str = "formal",
) -> dict[str, Any]:
    """Generate a tailored cover letter in markdown."""

    async def _run() -> CoverLetterGenerationResult:
        service = get_cover_letter_generation_service()
        return await service.generate(
            CoverLetterGenerationRequest(
                resume_text=resume_text,
                job_description=job_description,
                tone=cast(CoverLetterTone, tone),
            )
        )

    result = asyncio.run(_run())
    logger.info(
        "cover_letter_generated",
        extra={
            "task_id": self.request.id,
            "tone": tone,
            "result_length": len(result.cover_letter_markdown),
        },
    )
    return result.model_dump()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_email_notification(
    self,
    recipient_email: str,
    subject: str,
    body: str,
    content_type: str = "plain",
) -> dict[str, Any]:
    """Send an email notification through the configured SMTP server."""
    if not settings.smtp_host:
        raise RuntimeError("SMTP host is required for email notifications")

    sender = settings.smtp_from_address or settings.smtp_username
    if not sender:
        raise RuntimeError("SMTP from address or username is required for email notifications")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(body, subtype=content_type)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=settings.smtp_timeout_seconds,
    ) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    logger.info(
        "email_notification_sent",
        extra={
            "task_id": self.request.id,
            "recipient_email": recipient_email,
            "subject": subject,
        },
    )
    return {
        "status": "sent",
        "recipient_email": recipient_email,
        "subject": subject,
        "sender": sender,
    }
