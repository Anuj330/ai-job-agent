import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.modules.common import create_record
from app.modules.cover_letters.model import CoverLetter
from app.modules.cover_letters.schemas import CoverLetterCreate, CoverLetterRead

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


def _to_read(letter: CoverLetter) -> CoverLetterRead:
    """Serialize with job/resume relationships resolved to human labels."""
    return CoverLetterRead.model_validate(letter).model_copy(
        update={
            "job_title": letter.job.title if letter.job else None,
            "company": letter.job.company if letter.job else None,
            "resume_name": letter.resume.name if letter.resume else None,
        }
    )


@router.post("", response_model=CoverLetterRead, status_code=status.HTTP_201_CREATED)
async def create_cover_letter(payload: CoverLetterCreate, db: DB) -> CoverLetterRead:
    record = await create_record(db, CoverLetter, payload)
    return await get_cover_letter(record.id, db)


@router.get("", response_model=list[CoverLetterRead])
async def list_cover_letters(
    db: DB, offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50
) -> list[CoverLetterRead]:
    stmt = (
        select(CoverLetter)
        .options(selectinload(CoverLetter.job), selectinload(CoverLetter.resume))
        .offset(offset)
        .limit(limit)
    )
    return [_to_read(letter) for letter in await db.scalars(stmt)]


@router.get("/{cover_letter_id}", response_model=CoverLetterRead)
async def get_cover_letter(cover_letter_id: uuid.UUID, db: DB) -> CoverLetterRead:
    stmt = (
        select(CoverLetter)
        .where(CoverLetter.id == cover_letter_id)
        .options(selectinload(CoverLetter.job), selectinload(CoverLetter.resume))
    )
    letter = (await db.scalars(stmt)).first()
    if letter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    return _to_read(letter)
