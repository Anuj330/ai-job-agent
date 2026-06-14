import uuid
from typing import Literal

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=5)
    limit: int = Field(default=5, ge=1, le=20)


class JobSemanticHit(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str | None
    source: str
    source_url: str
    apply_url: str | None
    description: str | None
    experience_level: str | None
    experience_min_years: float | None
    experience_max_years: float | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    work_mode: Literal["remote", "hybrid", "onsite"] | None
    visa_sponsorship: bool | None
    skills: list[str]
    status: str
    created_at: str
    updated_at: str
    similarity: float = Field(ge=0, le=1)


class ResumeSemanticHit(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    owner_email: str
    content: str
    storage_url: str | None
    status: str
    created_at: str
    updated_at: str
    similarity: float = Field(ge=0, le=1)
