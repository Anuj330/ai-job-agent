"""Create initial domain tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260611_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("source_url", name=op.f("uq_jobs_source_url")),
    )
    op.create_index(op.f("ix_jobs_company"), "jobs", ["company"])
    op.create_index(op.f("ix_jobs_source"), "jobs", ["source"])
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"])
    op.create_index(op.f("ix_jobs_title"), "jobs", ["title"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_email", sa.String(length=320), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("storage_url", sa.String(length=2048), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resumes")),
    )
    op.create_index(op.f("ix_resumes_name"), "resumes", ["name"])
    op.create_index(op.f("ix_resumes_owner_email"), "resumes", ["owner_email"])
    op.create_index(op.f("ix_resumes_status"), "resumes", ["status"])

    op.create_table(
        "cover_letters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_cover_letters_job_id_jobs"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cover_letters")),
    )
    op.create_index(op.f("ix_cover_letters_job_id"), "cover_letters", ["job_id"])
    op.create_index(op.f("ix_cover_letters_status"), "cover_letters", ["status"])


def downgrade() -> None:
    op.drop_table("cover_letters")
    op.drop_table("resumes")
    op.drop_table("jobs")
