import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.common import create_record, get_record_or_404, list_records
from app.modules.resumes.model import Resume
from app.modules.semantic_search.schemas import ResumeSemanticHit
from app.modules.semantic_search.service import get_semantic_search_service
from app.modules.semantic_search.tasks import index_resume_embedding
from app.modules.resumes.schemas import ResumeCreate, ResumeRead

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume(payload: ResumeCreate, db: DB) -> Resume:
    resume = await create_record(db, Resume, payload)
    index_resume_embedding.delay(str(resume.id))
    return resume


@router.get("", response_model=list[ResumeRead])
async def list_resumes(
    db: DB, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50
) -> list[Resume]:
    return await list_records(db, Resume, offset=offset, limit=limit)


@router.get("/search", response_model=list[ResumeSemanticHit])
async def search_resumes(
    db: DB,
    query: Annotated[str, Query(min_length=5)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[ResumeSemanticHit]:
    service = get_semantic_search_service()
    return await service.search_resumes(db, query=query, limit=limit)


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(resume_id: uuid.UUID, db: DB) -> Resume:
    return await get_record_or_404(db, Resume, resume_id)
