"""Add LinkedIn job detail fields."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260611_0003"
down_revision: str | None = "20260611_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("apply_url", sa.String(length=2048), nullable=True))
    op.add_column("jobs", sa.Column("experience_level", sa.String(length=100), nullable=True))
    op.add_column("jobs", sa.Column("skills", sa.JSON(), server_default="[]", nullable=False))
    op.create_index(op.f("ix_jobs_experience_level"), "jobs", ["experience_level"])


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_experience_level"), table_name="jobs")
    op.drop_column("jobs", "skills")
    op.drop_column("jobs", "experience_level")
    op.drop_column("jobs", "apply_url")
