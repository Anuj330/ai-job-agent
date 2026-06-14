from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume


class BatchMatchRequest(BaseModel):
    resume_id: uuid.UUID
    # Score these jobs; if empty, score the most recent `limit` jobs.
    job_ids: list[uuid.UUID] = Field(default_factory=list)
    limit: int = Field(default=200, ge=1, le=500)


class BatchMatchResult(BaseModel):
    resume_id: uuid.UUID
    # job_id -> 0-100 fit score. Jobs with no usable skills are omitted so the UI
    # can hide the badge rather than show a fabricated number.
    scores: dict[str, int]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def score_job(resume_normalized: str, skills: list[str]) -> int | None:
    """Deterministic fit score: share of a job's distinct skills found in the resume."""
    cleaned = {_normalize(skill) for skill in skills if _normalize(skill)}
    if not cleaned:
        return None
    matched = sum(1 for skill in cleaned if skill in resume_normalized)
    return round(matched / len(cleaned) * 100)


class BatchMatchService:
    async def score(self, db: AsyncSession, request: BatchMatchRequest) -> BatchMatchResult:
        resume = await db.get(Resume, request.resume_id)
        if resume is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")
        resume_normalized = _normalize(resume.content)

        stmt = select(Job)
        if request.job_ids:
            stmt = stmt.where(Job.id.in_(request.job_ids))
        else:
            stmt = stmt.order_by(Job.created_at.desc()).limit(request.limit)

        scores: dict[str, int] = {}
        for job in await db.scalars(stmt):
            value = score_job(resume_normalized, list(job.skills or []))
            if value is not None:
                scores[str(job.id)] = value
        return BatchMatchResult(resume_id=request.resume_id, scores=scores)


def get_batch_match_service() -> BatchMatchService:
    return BatchMatchService()
