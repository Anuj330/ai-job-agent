from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.ai.matching import (
    MatchAnalysis,
    MatchAnalysisRequest,
    OpenAIMatchingService,
)
from app.modules.ai.router import get_matching_service


class FakeResponses:
    def __init__(self, parsed: MatchAnalysis) -> None:
        self.parsed = parsed
        self.calls: list[dict[str, object]] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


@pytest.mark.asyncio
async def test_matching_service_uses_structured_openai_output() -> None:
    parsed = MatchAnalysis(
        match_score=78,
        missing_skills=["Docker"],
        ats_keyword_recommendations=["Kubernetes", "CI/CD"],
        resume_improvement_suggestions=["Add quantified impact"],
        interview_focus_areas=["System design"],
    )
    client = SimpleNamespace(responses=FakeResponses(parsed))
    service = OpenAIMatchingService(client=client, model="gpt-4o-mini")

    result = await service.analyze(
        MatchAnalysisRequest(
            resume_text="Experienced Python engineer with SQL and APIs.",
            job_description="We need a Python engineer with SQL, Docker, and system design skills.",
        )
    )

    assert result == parsed
    assert client.responses.calls[0]["model"] == "gpt-4o-mini"
    assert "Resume:" in client.responses.calls[0]["input"]
    assert client.responses.calls[0]["text_format"] is MatchAnalysis


@pytest.mark.asyncio
async def test_ai_match_endpoint_returns_parsed_analysis() -> None:
    parsed = MatchAnalysis(
        match_score=92,
        missing_skills=[],
        ats_keyword_recommendations=["Python"],
        resume_improvement_suggestions=["Clarify recent impact"],
        interview_focus_areas=["Behavioral stories"],
    )
    calls: list[MatchAnalysisRequest] = []

    class FakeMatchingService:
        async def analyze(self, payload: MatchAnalysisRequest) -> MatchAnalysis:
            calls.append(payload)
            return parsed

    async def override_matching_service() -> FakeMatchingService:
        return FakeMatchingService()

    app.dependency_overrides[get_matching_service] = override_matching_service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/match",
                json={
                    "resume_text": "Experienced Python engineer with SQL and APIs.",
                    "job_description": (
                        "We need a Python engineer with SQL and system design skills."
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["match_score"] == 92
    assert len(calls) == 1
