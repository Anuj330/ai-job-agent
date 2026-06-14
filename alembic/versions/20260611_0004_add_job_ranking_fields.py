"""Add job ranking fields."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260611_0004"
down_revision: str | None = "20260611_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("experience_min_years", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("experience_max_years", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("salary_min", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("salary_max", sa.Float(), nullable=True))
    op.add_column("jobs", sa.Column("salary_currency", sa.String(length=3), nullable=True))
    op.add_column("jobs", sa.Column("work_mode", sa.String(length=20), nullable=True))
    op.add_column("jobs", sa.Column("visa_sponsorship", sa.Boolean(), nullable=True))
    op.create_index(op.f("ix_jobs_work_mode"), "jobs", ["work_mode"])


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_work_mode"), table_name="jobs")
    op.drop_column("jobs", "visa_sponsorship")
    op.drop_column("jobs", "work_mode")
    op.drop_column("jobs", "salary_currency")
    op.drop_column("jobs", "salary_max")
    op.drop_column("jobs", "salary_min")
    op.drop_column("jobs", "experience_max_years")
    op.drop_column("jobs", "experience_min_years")
