from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Boolean, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.applications.model import Application
    from app.modules.cover_letters.model import CoverLetter
    from app.modules.job_matches.model import JobMatch


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100), index=True)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True)
    apply_url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)
    experience_level: Mapped[str | None] = mapped_column(String(100), index=True)
    experience_min_years: Mapped[float | None] = mapped_column(Float)
    experience_max_years: Mapped[float | None] = mapped_column(Float)
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    work_mode: Mapped[str | None] = mapped_column(String(20), index=True)
    visa_sponsorship: Mapped[bool | None] = mapped_column(Boolean)
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(1536))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    status: Mapped[str] = mapped_column(
        String(50), default="discovered", server_default="discovered", index=True
    )

    matches: Mapped[list[JobMatch]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )
    cover_letters: Mapped[list[CoverLetter]] = relationship(
        back_populates="job", passive_deletes=True
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )
