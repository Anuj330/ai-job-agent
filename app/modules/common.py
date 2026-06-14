import uuid
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from pydantic_core import Url
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def create_record(db: AsyncSession, model: type[ModelT], payload: BaseModel) -> ModelT:
    values = {
        key: str(value) if isinstance(value, Url) else value
        for key, value in payload.model_dump().items()
    }
    record = model(**values)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_records(
    db: AsyncSession, model: type[ModelT], *, offset: int, limit: int
) -> list[ModelT]:
    result = await db.scalars(select(model).offset(offset).limit(limit))
    return list(result.all())


async def get_record_or_404(db: AsyncSession, model: type[ModelT], record_id: uuid.UUID) -> ModelT:
    record = await db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return record


def task_response(task: Any) -> dict[str, str]:
    return {"task_id": task.id, "status": "queued"}
