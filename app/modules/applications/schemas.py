import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ApplicationCreate(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    cover_letter_id: uuid.UUID | None = None
    status: str = "draft"
    applied_at: datetime | None = None
    external_url: HttpUrl | None = None
    notes: str | None = None


class ApplicationRead(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Resolved labels so the UI never shows raw UUIDs.
    job_title: str | None = None
    company: str | None = None
    resume_name: str | None = None
