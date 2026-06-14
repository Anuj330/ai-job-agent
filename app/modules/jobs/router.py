import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.common import create_record, get_record_or_404, list_records
from app.modules.jobs.model import Job
from app.modules.semantic_search.schemas import JobSemanticHit
from app.modules.semantic_search.service import get_semantic_search_service
from app.modules.semantic_search.tasks import index_job_embedding
from app.modules.jobs.ranking import (
    JobRankingRequest,
    JobRankingResult,
    JobRankingService,
    get_job_ranking_service,
)
from app.modules.jobs.schemas import JobCreate, JobRead

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: DB) -> Job:
    job = await create_record(db, Job, payload)
    index_job_embedding.delay(str(job.id))
    return job


@router.get("", response_model=list[JobRead])
async def list_jobs(
    db: DB, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50
) -> list[Job]:
    return await list_records(db, Job, offset=offset, limit=limit)


@router.get("/search", response_model=list[JobSemanticHit])
async def search_jobs(
    db: DB,
    query: Annotated[str, Query(min_length=5)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[JobSemanticHit]:
    service = get_semantic_search_service()
    return await service.search_jobs(db, query=query, limit=limit)


@router.post("/rank", response_model=JobRankingResult)
async def rank_jobs(
    payload: JobRankingRequest,
    service: Annotated[JobRankingService, Depends(get_job_ranking_service)],
) -> JSONResponse:
    result = service.rank_jobs(payload)
    return JSONResponse(content=result.model_dump())


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, db: DB) -> Job:
    return await get_record_or_404(db, Job, job_id)
