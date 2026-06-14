import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CoverLetterCreate(BaseModel):
    user_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    resume_id: uuid.UUID | None = None
    title: str
    content: str
    status: str = "draft"


class CoverLetterRead(CoverLetterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Resolved labels so the UI shows "Company — Title", never raw UUIDs.
    job_title: str | None = None
    company: str | None = None
    resume_name: str | None = None
