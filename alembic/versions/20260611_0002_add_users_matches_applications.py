"""Add users, job matches, applications, and ownership relationships."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260611_0002"
down_revision: str | None = "20260611_0001"
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
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"])
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"])

    op.add_column("resumes", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_resumes_user_id_users"),
        "resumes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"])

    op.add_column("cover_letters", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.add_column("cover_letters", sa.Column("resume_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_cover_letters_user_id_users"),
        "cover_letters",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_cover_letters_resume_id_resumes"),
        "cover_letters",
        "resumes",
        ["resume_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_cover_letters_user_id"), "cover_letters", ["user_id"])
    op.create_index(op.f("ix_cover_letters_resume_id"), "cover_letters", ["resume_id"])

    op.create_table(
        "job_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="new", nullable=False),
        *timestamps(),
        sa.CheckConstraint("score >= 0 AND score <= 1", name=op.f("ck_job_matches_score_range")),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_job_matches_job_id_jobs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            name=op.f("fk_job_matches_resume_id_resumes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_job_matches_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_matches")),
        sa.UniqueConstraint(
            "user_id", "job_id", "resume_id", name="uq_job_matches_user_job_resume"
        ),
    )
    op.create_index(op.f("ix_job_matches_job_id"), "job_matches", ["job_id"])
    op.create_index(op.f("ix_job_matches_resume_id"), "job_matches", ["resume_id"])
    op.create_index(op.f("ix_job_matches_score"), "job_matches", ["score"])
    op.create_index(op.f("ix_job_matches_status"), "job_matches", ["status"])
    op.create_index(op.f("ix_job_matches_user_id"), "job_matches", ["user_id"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("cover_letter_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="draft", nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["cover_letter_id"],
            ["cover_letters.id"],
            name=op.f("fk_applications_cover_letter_id_cover_letters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_applications_job_id_jobs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            name=op.f("fk_applications_resume_id_resumes"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_applications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )
    op.create_index(op.f("ix_applications_applied_at"), "applications", ["applied_at"])
    op.create_index(op.f("ix_applications_cover_letter_id"), "applications", ["cover_letter_id"])
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"])
    op.create_index(op.f("ix_applications_resume_id"), "applications", ["resume_id"])
    op.create_index(op.f("ix_applications_status"), "applications", ["status"])
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"])


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("job_matches")

    op.drop_index(op.f("ix_cover_letters_resume_id"), table_name="cover_letters")
    op.drop_index(op.f("ix_cover_letters_user_id"), table_name="cover_letters")
    op.drop_constraint(
        op.f("fk_cover_letters_resume_id_resumes"), "cover_letters", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_cover_letters_user_id_users"), "cover_letters", type_="foreignkey")
    op.drop_column("cover_letters", "resume_id")
    op.drop_column("cover_letters", "user_id")

    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_constraint(op.f("fk_resumes_user_id_users"), "resumes", type_="foreignkey")
    op.drop_column("resumes", "user_id")

    op.drop_table("users")
