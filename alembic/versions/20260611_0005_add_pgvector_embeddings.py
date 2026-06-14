"""Add pgvector embeddings for jobs and resumes."""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

from alembic import op

revision: str = "20260611_0005"
down_revision: str | None = "20260611_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("jobs", sa.Column("embedding", VECTOR(1536), nullable=True))
    op.add_column("resumes", sa.Column("embedding", VECTOR(1536), nullable=True))
    op.create_index(
        "ix_jobs_embedding_hnsw",
        "jobs",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_resumes_embedding_hnsw",
        "resumes",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_resumes_embedding_hnsw", table_name="resumes")
    op.drop_index("ix_jobs_embedding_hnsw", table_name="jobs")
    op.drop_column("resumes", "embedding")
    op.drop_column("jobs", "embedding")
