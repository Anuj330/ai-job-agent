from __future__ import annotations

from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.ai.matching import create_openai_client

CoverLetterTone = Literal["formal", "startup", "enterprise"]


class CoverLetterGenerationRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    job_description: str = Field(min_length=20)
    tone: CoverLetterTone = "formal"


class CoverLetterGenerationResult(BaseModel):
    cover_letter_markdown: str = Field(min_length=20)


class OpenAICoverLetterGenerationService:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def generate(self, request: CoverLetterGenerationRequest) -> CoverLetterGenerationResult:
        tone_guidance = {
            "formal": "Use a polished, respectful, and direct tone.",
            "startup": "Use an energetic, concise, and pragmatic tone.",
            "enterprise": "Use a measured, professional, and outcome-oriented tone.",
        }[request.tone]
        prompt = (
            "Write a concise, human sounding cover letter tailored to the job description. "
            "Avoid generic AI phrasing, filler, and exaggerated claims. Use only details "
            "supported by the resume or clearly implied by the job description. Keep it "
            "brief and specific.\n\n"
            f"Tone guidance: {tone_guidance}\n\n"
            "Return the final cover letter as markdown only.\n\n"
            f"Resume text:\n{request.resume_text}\n\n"
            f"Job description:\n{request.job_description}"
        )
        response = await self.client.responses.parse(
            model=self.model,
            input=prompt,
            instructions=(
                "You are a cover letter generator for hiring workflows. Return only "
                "structured output that follows the schema exactly. Preserve a natural "
                "human voice and do not add commentary outside the cover letter."
            ),
            text_format=CoverLetterGenerationResult,
            temperature=0.5,
            max_output_tokens=900,
        )
        result = response.output_parsed
        if result is None:
            raise RuntimeError("OpenAI returned no parsed cover letter")
        return result


def get_cover_letter_generation_service() -> OpenAICoverLetterGenerationService:
    return OpenAICoverLetterGenerationService(
        create_openai_client(),
        settings.openai_matching_model,
    )
