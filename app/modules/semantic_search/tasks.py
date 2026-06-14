from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume
from app.modules.semantic_search.service import (
    build_job_embedding_text,
    build_resume_embedding_text,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def index_job_embedding(self, job_id: str) -> dict[str, Any]:
    return asyncio.run(_index_job_embedding(job_id))


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def index_resume_embedding(self, resume_id: str) -> dict[str, Any]:
    return asyncio.run(_index_resume_embedding(resume_id))


async def _index_job_embedding(job_id: str) -> dict[str, Any]:
    async with SessionLocal() as db:
        job = await db.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        job.embedding = await get_embedding_service().embed(build_job_embedding_text(job))
        await db.commit()
    logger.info("job_embedding_indexed", extra={"job_id": job_id})
    return {"status": "indexed", "job_id": job_id}


async def _index_resume_embedding(resume_id: str) -> dict[str, Any]:
    async with SessionLocal() as db:
        resume = await db.get(Resume, resume_id)
        if resume is None:
            raise ValueError(f"Resume not found: {resume_id}")
        resume.embedding = await get_embedding_service().embed(build_resume_embedding_text(resume))
        await db.commit()
    logger.info("resume_embedding_indexed", extra={"resume_id": resume_id})
    return {"status": "indexed", "resume_id": resume_id}
