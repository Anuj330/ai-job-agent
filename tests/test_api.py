from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_openapi_contains_domain_routes() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        paths = (await client.get("/openapi.json")).json()["paths"]

    assert "/api/v1/jobs" in paths
    assert "/api/v1/jobs/search" in paths
    assert "/api/v1/jobs/rank" in paths
    assert "/api/v1/applications" in paths
    assert "/api/v1/resumes" in paths
    assert "/api/v1/resumes/search" in paths
    assert "/api/v1/cover-letters" in paths
    assert "/api/v1/scrapers/runs" in paths
    assert "/api/v1/scrapers/linkedin/runs" in paths
    assert "/api/v1/scrapers/naukri/runs" in paths
    assert "/api/v1/scrapers/bayt/runs" in paths
    assert "/api/v1/scrapers/indeed/runs" in paths
    assert "/api/v1/ai/generations" in paths
    assert "/api/v1/ai/match" in paths
    assert "/api/v1/ai/match/batch" in paths
    assert "/api/v1/ai/resume-optimization" in paths
    assert "/api/v1/ai/cover-letter" in paths
    assert "/api/v1/ai/resume-shortlist" in paths
    assert "/api/v1/ai/visibility" in paths
    assert "/api/v1/stats" in paths
