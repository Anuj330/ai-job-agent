import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeCreate(BaseModel):
    user_id: uuid.UUID | None = None
    name: str
    owner_email: str
    content: str
    storage_url: str | None = None
    status: str = "draft"


class ResumeRead(ResumeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
