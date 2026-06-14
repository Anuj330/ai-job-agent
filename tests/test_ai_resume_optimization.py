from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.ai.resume_optimization import (
    OpenAIResumeOptimizationService,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    get_resume_optimization_service,
)


class FakeResponses:
    def __init__(self, parsed: ResumeOptimizationResult) -> None:
        self.parsed = parsed
        self.calls: list[dict[str, object]] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


@pytest.mark.asyncio
async def test_resume_optimization_service_uses_structured_openai_output() -> None:
    parsed = ResumeOptimizationResult(
        optimized_markdown="# Resume\n\n## Summary\nOptimized summary",
    )
    client = SimpleNamespace(responses=FakeResponses(parsed))
    service = OpenAIResumeOptimizationService(client=client, model="gpt-4o-mini")

    result = await service.optimize(
        ResumeOptimizationRequest(
            resume_markdown="# Resume\n\n## Summary\nOriginal summary",
            job_description=(
                "We need a Python engineer with SQL, Docker, and strong communication skills."
            ),
        )
    )

    assert result == parsed
    assert client.responses.calls[0]["model"] == "gpt-4o-mini"
    assert "Resume markdown:" in client.responses.calls[0]["input"]
    assert client.responses.calls[0]["text_format"] is ResumeOptimizationResult


@pytest.mark.asyncio
async def test_ai_resume_optimization_endpoint_returns_optimized_markdown() -> None:
    parsed = ResumeOptimizationResult(optimized_markdown="# Resume\n\n## Summary\nOptimized")
    calls: list[ResumeOptimizationRequest] = []

    class FakeResumeOptimizationService:
        async def optimize(self, payload: ResumeOptimizationRequest) -> ResumeOptimizationResult:
            calls.append(payload)
            return parsed

    async def override_resume_optimization_service() -> FakeResumeOptimizationService:
        return FakeResumeOptimizationService()

    app.dependency_overrides[get_resume_optimization_service] = override_resume_optimization_service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/resume-optimization",
                json={
                    "resume_markdown": "# Resume\n\n## Summary\nOriginal",
                    "job_description": (
                        "We need a Python engineer with SQL, Docker, and communication skills."
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["optimized_markdown"] == "# Resume\n\n## Summary\nOptimized"
    assert len(calls) == 1
