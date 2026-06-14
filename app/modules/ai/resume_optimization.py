from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.ai.matching import create_openai_client


class ResumeOptimizationRequest(BaseModel):
    resume_markdown: str = Field(min_length=20)
    job_description: str = Field(min_length=20)


class ResumeOptimizationResult(BaseModel):
    optimized_markdown: str = Field(min_length=20)


class OpenAIResumeOptimizationService:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def optimize(self, request: ResumeOptimizationRequest) -> ResumeOptimizationResult:
        prompt = (
            "Optimize the resume for the provided job description while preserving the "
            "original markdown structure and formatting as closely as possible. Keep the "
            "same section order, headings, bullet style, and overall layout unless a small "
            "edit is required for clarity.\n\n"
            "Rewrite only these areas when needed: summary, skills, and project descriptions. "
            "Inject ATS keywords naturally, based on the job description, without stuffing, "
            "fabrication, or adding unrelated claims. Keep the original voice professional, "
            "specific, and concise.\n\n"
            "Return the full optimized resume as markdown only.\n\n"
            f"Resume markdown:\n{request.resume_markdown}\n\n"
            f"Job description:\n{request.job_description}"
        )
        response = await self.client.responses.parse(
            model=self.model,
            input=prompt,
            instructions=(
                "You are a resume optimization engine. Return only structured output "
                "that follows the schema exactly. Preserve markdown formatting and do "
                "not add commentary outside the optimized resume."
            ),
            text_format=ResumeOptimizationResult,
            temperature=0.2,
            max_output_tokens=1500,
        )
        result = response.output_parsed
        if result is None:
            raise RuntimeError("OpenAI returned no parsed resume optimization")
        return result


def get_resume_optimization_service() -> OpenAIResumeOptimizationService:
    return OpenAIResumeOptimizationService(create_openai_client(), settings.openai_matching_model)
