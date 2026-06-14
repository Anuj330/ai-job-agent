import json

import pytest

from app.modules.jobs.ranking import (
    JobRankingCandidateProfile,
    JobRankingJob,
    JobRankingRequest,
    JobRankingService,
)
from app.modules.jobs.router import rank_jobs


def test_job_ranking_service_orders_jobs_by_weighted_fit() -> None:
    service = JobRankingService()
    request = JobRankingRequest(
        candidate=JobRankingCandidateProfile(
            skills=["Python", "SQL", "Docker"],
            preferred_locations=["Austin, TX"],
            desired_salary=140_000,
            salary_currency="USD",
            experience_years=5,
            remote_preference="hybrid",
            requires_visa_sponsorship=True,
        ),
        jobs=[
            JobRankingJob(
                id=None,
                title="Backend Engineer",
                company="RemoteCo",
                location="Austin, TX",
                skills=["Python", "SQL", "AWS"],
                salary_min=130_000,
                salary_max=155_000,
                salary_currency="USD",
                work_mode="hybrid",
                visa_sponsorship=True,
                experience_min_years=4,
                experience_max_years=7,
            ),
            JobRankingJob(
                id=None,
                title="Platform Engineer",
                company="FarAway Inc",
                location="London, UK",
                skills=["Go", "Kubernetes"],
                salary_min=160_000,
                salary_max=180_000,
                salary_currency="USD",
                work_mode="onsite",
                visa_sponsorship=False,
                experience_min_years=8,
                experience_max_years=10,
            ),
        ],
    )

    result = service.rank_jobs(request)

    assert result.ranked_jobs[0].title == "Backend Engineer"
    assert result.ranked_jobs[0].score > result.ranked_jobs[1].score
    assert result.ranked_jobs[0].factors.visa_sponsorship == 1.0
    assert result.ranked_jobs[1].factors.skills_match == 0.0


@pytest.mark.asyncio
async def test_job_ranking_endpoint_returns_ranked_jobs() -> None:
    payload = JobRankingRequest(
        candidate=JobRankingCandidateProfile(
            skills=["Python", "SQL", "Docker"],
            preferred_locations=["Austin, TX"],
            desired_salary=140000,
            salary_currency="USD",
            experience_years=5,
            remote_preference="hybrid",
            requires_visa_sponsorship=True,
        ),
        jobs=[
            JobRankingJob(
                title="Backend Engineer",
                company="RemoteCo",
                location="Austin, TX",
                skills=["Python", "SQL", "AWS"],
                salary_min=130000,
                salary_max=155000,
                salary_currency="USD",
                work_mode="hybrid",
                visa_sponsorship=True,
                experience_min_years=4,
                experience_max_years=7,
            ),
            JobRankingJob(
                title="Platform Engineer",
                company="FarAway Inc",
                location="London, UK",
                skills=["Go", "Kubernetes"],
                salary_min=160000,
                salary_max=180000,
                salary_currency="USD",
                work_mode="onsite",
                visa_sponsorship=False,
                experience_min_years=8,
                experience_max_years=10,
            ),
        ],
    )

    response = await rank_jobs(payload, JobRankingService())

    assert response.status_code == 200
    data = json.loads(response.body)
    assert len(data["ranked_jobs"]) == 2
    assert data["ranked_jobs"][0]["title"] == "Backend Engineer"
