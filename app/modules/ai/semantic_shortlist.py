from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.ai.openai_client import create_openai_client
from app.modules.semantic_search.schemas import ResumeSemanticHit
from app.modules.semantic_search.service import get_semantic_search_service


class ResumeShortlistRequest(BaseModel):
    job_description: str = Field(min_length=20)
    top_k: int = Field(default=5, ge=1, le=20)


class ResumeShortlistMatch(BaseModel):
    resume_id: str
    resume_name: str
    similarity: float = Field(ge=0, le=1)
    rationale: str


class ResumeShortlistAnalysis(BaseModel):
    summary: str
    shortlisted_resumes: list[ResumeShortlistMatch]


class OpenAIResumeShortlistService:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def shortlist(
        self, db: AsyncSession, request: ResumeShortlistRequest
    ) -> ResumeShortlistAnalysis:
        search_service = get_semantic_search_service()
        candidates = await search_service.search_resumes(
            db, query=request.job_description, limit=request.top_k
        )
        prompt = self._build_prompt(request.job_description, candidates)
        response = await self.client.responses.parse(
            model=self.model,
            input=prompt,
            instructions=(
                "You are a hiring assistant. Review only the retrieved top semantic matches and "
                "return a concise shortlist. Do not mention candidates outside the retrieved set."
            ),
            text_format=ResumeShortlistAnalysis,
            temperature=0.2,
            max_output_tokens=900,
        )
        result = response.output_parsed
        if result is None:
            raise RuntimeError("OpenAI returned no parsed resume shortlist")
        return result

    @staticmethod
    def _build_prompt(job_description: str, candidates: list[ResumeSemanticHit]) -> str:
        lines = ["Job description:", job_description, "", "Retrieved resumes:"]
        for candidate in candidates:
            lines.append(
                f"- {candidate.name} ({candidate.id}) similarity={candidate.similarity:.3f}\n"
                f"  excerpt: {candidate.content[:600]}"
            )
        return "\n".join(lines)


def get_resume_shortlist_service() -> OpenAIResumeShortlistService:
    return OpenAIResumeShortlistService(create_openai_client(), settings.openai_matching_model)
