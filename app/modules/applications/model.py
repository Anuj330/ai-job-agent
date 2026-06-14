from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.cover_letters.model import CoverLetter
    from app.modules.jobs.model import Job
    from app.modules.resumes.model import Resume
    from app.modules.users.model import User


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="SET NULL"), index=True
    )
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cover_letters.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="draft", server_default="draft", index=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    external_url: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    resume: Mapped[Resume | None] = relationship(back_populates="applications")
    cover_letter: Mapped[CoverLetter | None] = relationship(back_populates="applications")
