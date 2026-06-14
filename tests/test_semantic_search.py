from types import SimpleNamespace

import pytest

from app.modules.ai.semantic_shortlist import (
    OpenAIResumeShortlistService,
    ResumeShortlistAnalysis,
    ResumeShortlistMatch,
    ResumeShortlistRequest,
)
from app.modules.semantic_search.service import OpenAIEmbeddingService, build_job_embedding_text


def test_build_job_embedding_text_uses_semantic_fields() -> None:
    job = SimpleNamespace(
        title="Senior Python Engineer",
        company="Acme",
        location="Remote",
        description="Build APIs and data pipelines",
        skills=["Python", "SQL"],
        experience_level="Senior",
        work_mode="remote",
        visa_sponsorship=True,
    )

    text = build_job_embedding_text(job)

    assert "Senior Python Engineer" in text
    assert "Python, SQL" in text
    assert "visa sponsorship" in text


@pytest.mark.asyncio
async def test_embedding_service_uses_openai_embeddings_endpoint() -> None:
    class FakeEmbeddings:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])]
            )

    client = SimpleNamespace(embeddings=FakeEmbeddings())
    service = OpenAIEmbeddingService(client=client, model="text-embedding-3-small")

    embedding = await service.embed("Senior Python engineer")

    assert embedding == [0.1, 0.2, 0.3]
    assert client.embeddings.calls[0]["model"] == "text-embedding-3-small"
    assert client.embeddings.calls[0]["input"] == "Senior Python engineer"


@pytest.mark.asyncio
async def test_resume_shortlist_uses_retrieved_candidates_only(monkeypatch: pytest.MonkeyPatch) -> None:
    retrieved = [
        SimpleNamespace(
            id="resume-1",
            name="Resume One",
            content="Python, SQL, APIs",
            similarity=0.92,
        ),
        SimpleNamespace(
            id="resume-2",
            name="Resume Two",
            content="Django, FastAPI, PostgreSQL",
            similarity=0.86,
        ),
    ]

    class FakeSearchService:
        async def search_resumes(self, db, query: str, limit: int = 5):
            assert query.startswith("Build backend services")
            assert limit == 2
            return retrieved

    class FakeResponses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def parse(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(
                output_parsed=ResumeShortlistAnalysis(
                    summary="Top two resumes are strongest.",
                    shortlisted_resumes=[
                        ResumeShortlistMatch(
                            resume_id="resume-1",
                            resume_name="Resume One",
                            similarity=0.92,
                            rationale="Best skill overlap",
                        )
                    ],
                )
            )

    fake_client = SimpleNamespace(responses=FakeResponses())

    monkeypatch.setattr(
        "app.modules.ai.semantic_shortlist.get_semantic_search_service",
        lambda: FakeSearchService(),
    )

    service = OpenAIResumeShortlistService(client=fake_client, model="gpt-4o-mini")

    result = await service.shortlist(
        db=SimpleNamespace(),
        request=ResumeShortlistRequest(job_description="Build backend services with Python", top_k=2),
    )

    assert result.summary == "Top two resumes are strongest."
    prompt = fake_client.responses.calls[0]["input"]
    assert "Resume One" in prompt
    assert "Resume Two" in prompt
    assert "Build backend services with Python" in prompt
