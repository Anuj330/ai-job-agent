from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.ai.openai_client import create_openai_client


class MatchAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100)
    missing_skills: list[str] = Field(default_factory=list)
    ats_keyword_recommendations: list[str] = Field(default_factory=list)
    resume_improvement_suggestions: list[str] = Field(default_factory=list)
    interview_focus_areas: list[str] = Field(default_factory=list)


class MatchAnalysisRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    job_description: str = Field(min_length=20)


class OpenAIMatchingService:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def analyze(self, request: MatchAnalysisRequest) -> MatchAnalysis:
        prompt = (
            "Compare the resume against the job description and return a concise, "
            "actionable analysis. Be strict about only recommending skills and "
            "keywords that are present or clearly implied. Do not invent experience. "
            "Focus on ATS optimization and interview preparation.\n\n"
            f"Resume:\n{request.resume_text}\n\n"
            f"Job description:\n{request.job_description}"
        )
        response = await self.client.responses.parse(
            model=self.model,
            input=prompt,
            instructions=(
                "You are an AI matching engine for hiring workflows. "
                "Return only structured output that follows the schema exactly. "
                "Use a match_score from 0 to 100."
            ),
            text_format=MatchAnalysis,
            temperature=0.2,
            max_output_tokens=700,
        )
        result = response.output_parsed
        if result is None:
            raise RuntimeError("OpenAI returned no parsed matching analysis")
        return result


def get_matching_service() -> OpenAIMatchingService:
    return OpenAIMatchingService(create_openai_client(), settings.openai_matching_model)
