import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.modules.applications.model import Application
from app.modules.applications.schemas import ApplicationCreate, ApplicationRead
from app.modules.common import create_record

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


def _to_read(application: Application) -> ApplicationRead:
    """Serialize with job/resume relationships resolved to human labels."""
    return ApplicationRead.model_validate(application).model_copy(
        update={
            "job_title": application.job.title if application.job else None,
            "company": application.job.company if application.job else None,
            "resume_name": application.resume.name if application.resume else None,
        }
    )


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate, db: DB) -> ApplicationRead:
    record = await create_record(db, Application, payload)
    return await get_application(record.id, db)


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    db: DB, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50
) -> list[ApplicationRead]:
    stmt = (
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.resume))
        .offset(offset)
        .limit(limit)
    )
    return [_to_read(application) for application in await db.scalars(stmt)]


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: uuid.UUID, db: DB) -> ApplicationRead:
    stmt = (
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.job), selectinload(Application.resume))
    )
    application = (await db.scalars(stmt)).first()
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    return _to_read(application)
