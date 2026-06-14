from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.ai.cover_letter_generation import (
    CoverLetterGenerationRequest,
    CoverLetterGenerationResult,
    OpenAICoverLetterGenerationService,
    get_cover_letter_generation_service,
)


class FakeResponses:
    def __init__(self, parsed: CoverLetterGenerationResult) -> None:
        self.parsed = parsed
        self.calls: list[dict[str, object]] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


@pytest.mark.asyncio
async def test_cover_letter_service_uses_structured_openai_output() -> None:
    parsed = CoverLetterGenerationResult(
        cover_letter_markdown=(
            "Dear Hiring Team,\n\n"
            "I’m excited to apply for this role because the work aligns with my "
            "background in Python, SQL, and building reliable products.\n\n"
            "Best regards,\nCandidate"
        )
    )
    client = SimpleNamespace(responses=FakeResponses(parsed))
    service = OpenAICoverLetterGenerationService(client=client, model="gpt-4o-mini")

    result = await service.generate(
        CoverLetterGenerationRequest(
            resume_text="Experienced Python engineer with SQL, APIs, and product delivery.",
            job_description=(
                "We need a Python engineer who can work with SQL, APIs, and cross-functional teams."
            ),
            tone="formal",
        )
    )

    assert result == parsed
    assert client.responses.calls[0]["model"] == "gpt-4o-mini"
    assert "Resume text:" in client.responses.calls[0]["input"]
    assert client.responses.calls[0]["text_format"] is CoverLetterGenerationResult


@pytest.mark.asyncio
async def test_ai_cover_letter_endpoint_returns_markdown() -> None:
    parsed = CoverLetterGenerationResult(
        cover_letter_markdown=(
            "Dear Hiring Team,\n\nI’d love to contribute.\n\nBest regards,\nCandidate"
        )
    )
    calls: list[CoverLetterGenerationRequest] = []

    class FakeCoverLetterService:
        async def generate(
            self, payload: CoverLetterGenerationRequest
        ) -> CoverLetterGenerationResult:
            calls.append(payload)
            return parsed

    async def override_cover_letter_service() -> FakeCoverLetterService:
        return FakeCoverLetterService()

    app.dependency_overrides[get_cover_letter_generation_service] = override_cover_letter_service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/cover-letter",
                json={
                    "resume_text": (
                        "Experienced Python engineer with SQL, APIs, and product delivery."
                    ),
                    "job_description": (
                        "We need a Python engineer who can work with SQL, APIs, and "
                        "cross-functional teams."
                    ),
                    "tone": "startup",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["cover_letter_markdown"].startswith("Dear Hiring Team")
    assert len(calls) == 1
