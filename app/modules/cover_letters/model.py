from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.applications.model import Application
    from app.modules.jobs.model import Job
    from app.modules.resumes.model import Resume
    from app.modules.users.model import User


class CoverLetter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cover_letters"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50), default="draft", server_default="draft", index=True
    )

    user: Mapped[User | None] = relationship(back_populates="cover_letters")
    job: Mapped[Job | None] = relationship(back_populates="cover_letters")
    resume: Mapped[Resume | None] = relationship(back_populates="cover_letters")
    applications: Mapped[list[Application]] = relationship(
        back_populates="cover_letter", passive_deletes=True
    )
