from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.applications.model import Application
    from app.modules.cover_letters.model import CoverLetter
    from app.modules.job_matches.model import JobMatch
    from app.modules.resumes.model import Resume


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", index=True
    )

    resumes: Mapped[list[Resume]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    job_matches: Mapped[list[JobMatch]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    cover_letters: Mapped[list[CoverLetter]] = relationship(
        back_populates="user", passive_deletes=True
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
