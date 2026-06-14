from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.applications.model import Application
    from app.modules.cover_letters.model import CoverLetter
    from app.modules.job_matches.model import JobMatch
    from app.modules.users.model import User


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    owner_email: Mapped[str] = mapped_column(String(320), index=True)
    content: Mapped[str] = mapped_column(Text)
    storage_url: Mapped[str | None] = mapped_column(String(2048))
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(1536))
    status: Mapped[str] = mapped_column(
        String(50), default="draft", server_default="draft", index=True
    )

    user: Mapped[User | None] = relationship(back_populates="resumes")
    job_matches: Mapped[list[JobMatch]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", passive_deletes=True
    )
    cover_letters: Mapped[list[CoverLetter]] = relationship(
        back_populates="resume", passive_deletes=True
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="resume", passive_deletes=True
    )
