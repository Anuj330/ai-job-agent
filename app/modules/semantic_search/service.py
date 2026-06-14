from __future__ import annotations

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ai.openai_client import create_openai_client
from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume
from app.modules.semantic_search.schemas import JobSemanticHit, ResumeSemanticHit


def build_job_embedding_text(job: Job) -> str:
    parts = [
        job.title,
        job.company,
        job.location or "",
        job.description or "",
        ", ".join(job.skills),
        job.experience_level or "",
        job.work_mode or "",
        "visa sponsorship" if job.visa_sponsorship else "no visa sponsorship",
    ]
    return "\n".join(part for part in parts if part).strip()


def build_resume_embedding_text(resume: Resume) -> str:
    parts = [resume.name, resume.owner_email, resume.content]
    return "\n".join(part for part in parts if part).strip()


class OpenAIEmbeddingService:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text.replace("\n", " "),
            encoding_format="float",
        )
        embedding = response.data[0].embedding
        if embedding is None:
            raise RuntimeError("OpenAI returned no embedding vector")
        return list(embedding)


class SemanticSearchService:
    def __init__(self, embedding_service: OpenAIEmbeddingService) -> None:
        self.embedding_service = embedding_service

    async def search_jobs(self, db: AsyncSession, query: str, limit: int = 5) -> list[JobSemanticHit]:
        embedding = await self.embedding_service.embed(query)
        distance = Job.embedding.cosine_distance(embedding)
        stmt = (
            select(Job, distance.label("distance"))
            .where(Job.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [self._job_hit(job, distance) for job, distance in rows]

    async def search_resumes(
        self, db: AsyncSession, query: str, limit: int = 5
    ) -> list[ResumeSemanticHit]:
        embedding = await self.embedding_service.embed(query)
        distance = Resume.embedding.cosine_distance(embedding)
        stmt = (
            select(Resume, distance.label("distance"))
            .where(Resume.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [self._resume_hit(resume, distance) for resume, distance in rows]

    @staticmethod
    def _similarity(distance: float | None) -> float:
        if distance is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - float(distance)))

    def _job_hit(self, job: Job, distance: float | None) -> JobSemanticHit:
        payload = job.__dict__.copy()
        payload.pop("_sa_instance_state", None)
        payload["similarity"] = self._similarity(distance)
        return JobSemanticHit.model_validate(payload)

    def _resume_hit(self, resume: Resume, distance: float | None) -> ResumeSemanticHit:
        payload = resume.__dict__.copy()
        payload.pop("_sa_instance_state", None)
        payload["similarity"] = self._similarity(distance)
        return ResumeSemanticHit.model_validate(payload)


def get_embedding_service() -> OpenAIEmbeddingService:
    return OpenAIEmbeddingService(create_openai_client(), settings.openai_embedding_model)


def get_semantic_search_service() -> SemanticSearchService:
    return SemanticSearchService(get_embedding_service())
