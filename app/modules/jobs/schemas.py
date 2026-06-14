import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobCreate(BaseModel):
    title: str
    company: str
    location: str | None = None
    source: str
    source_url: HttpUrl
    apply_url: HttpUrl | None = None
    description: str | None = None
    experience_level: str | None = None
    experience_min_years: float | None = Field(default=None, ge=0)
    experience_max_years: float | None = Field(default=None, ge=0)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None
    visa_sponsorship: bool | None = None
    skills: list[str] = Field(default_factory=list)
    status: str = "discovered"


class JobRead(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
