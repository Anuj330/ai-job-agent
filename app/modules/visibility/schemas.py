from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator


class KeywordDemand(BaseModel):
    """A single market keyword and how often recruiters' postings demand it."""

    keyword: str
    demand_pct: float = Field(ge=0, le=100)
    postings: int = Field(ge=0)


class VisibilityRequest(BaseModel):
    # Supply either a stored resume (resume_id) or raw resume_text.
    resume_id: uuid.UUID | None = None
    resume_text: str | None = Field(default=None, min_length=20)
    target_role: str = Field(min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    top_keywords: int = Field(default=25, ge=5, le=100)
    sample_size: int = Field(default=200, ge=10, le=1000)

    @model_validator(mode="after")
    def _require_resume_source(self) -> VisibilityRequest:
        if self.resume_id is None and not (self.resume_text and self.resume_text.strip()):
            raise ValueError("Provide either resume_id or resume_text")
        return self


class VisibilityResult(BaseModel):
    target_role: str
    location: str | None = None
    analyzed_postings: int = Field(ge=0)
    # Weighted share of in-demand keywords the resume already covers (0-100).
    visibility_score: int = Field(ge=0, le=100)
    present_keywords: list[KeywordDemand] = Field(default_factory=list)
    missing_keywords: list[KeywordDemand] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
