from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.applications.model import Application
from app.modules.cover_letters.model import CoverLetter
from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]

# Statuses that count as "done" for each pipeline-pulse bar.
_OPTIMIZED_RESUME_STATUSES = ("optimized", "ready")
_SUBMITTED_APPLICATION_STATUSES = ("applied", "interview", "offer", "rejected")


class PipelinePulse(BaseModel):
    jobs_analyzed_pct: int
    resumes_optimized_pct: int
    applications_submitted_pct: int


class DashboardStats(BaseModel):
    jobs: int
    resumes: int
    cover_letters: int
    applications: int
    pulse: PipelinePulse


def _pct(part: int, whole: int) -> int:
    return round(part / whole * 100) if whole else 0


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.scalar(stmt)) or 0)


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(db: DB) -> DashboardStats:
    jobs = await _count(db, select(func.count()).select_from(Job))
    resumes = await _count(db, select(func.count()).select_from(Resume))
    cover_letters = await _count(db, select(func.count()).select_from(CoverLetter))
    applications = await _count(db, select(func.count()).select_from(Application))

    # "Analyzed" jobs = those with an embedding indexed; "optimized" resumes and
    # "submitted" applications are derived from their status fields.
    jobs_analyzed = await _count(
        db, select(func.count()).select_from(Job).where(Job.embedding.is_not(None))
    )
    resumes_optimized = await _count(
        db,
        select(func.count())
        .select_from(Resume)
        .where(Resume.status.in_(_OPTIMIZED_RESUME_STATUSES)),
    )
    applications_submitted = await _count(
        db,
        select(func.count())
        .select_from(Application)
        .where(Application.status.in_(_SUBMITTED_APPLICATION_STATUSES)),
    )

    return DashboardStats(
        jobs=jobs,
        resumes=resumes,
        cover_letters=cover_letters,
        applications=applications,
        pulse=PipelinePulse(
            jobs_analyzed_pct=_pct(jobs_analyzed, jobs),
            resumes_optimized_pct=_pct(resumes_optimized, resumes),
            applications_submitted_pct=_pct(applications_submitted, applications),
        ),
    )
