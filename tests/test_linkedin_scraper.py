from unittest.mock import AsyncMock

import pytest

from app.modules.scrapers.base import SearchRequest
from app.modules.scrapers.bayt import BaytScraper, load_bayt_cookies
from app.modules.scrapers.linkedin import (
    LinkedInJob,
    LinkedInScraper,
    load_linkedin_cookies,
    save_linkedin_jobs,
)
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies


def test_load_linkedin_cookies() -> None:
    assert load_linkedin_cookies('[{"name": "li_at", "value": "secret"}]') == [
        {"name": "li_at", "value": "secret"}
    ]


@pytest.mark.parametrize("raw_json", ["invalid", "{}", "[1]"])
def test_load_linkedin_cookies_rejects_invalid_values(raw_json: str) -> None:
    with pytest.raises(ValueError):
        load_linkedin_cookies(raw_json)


def test_extract_experience_and_skills() -> None:
    description = """
    This is a Mid-Senior level role.

    Required skills: Python, PostgreSQL; FastAPI
    """

    assert LinkedInScraper._extract_experience_level(description) == "Mid-Senior Level"
    assert LinkedInScraper._extract_skills(description) == ["Python", "PostgreSQL", "FastAPI"]


async def test_save_linkedin_jobs_executes_postgres_upsert() -> None:
    db = AsyncMock()
    jobs = [
        LinkedInJob(
            title="Backend Engineer",
            company="Example",
            source_url="https://www.linkedin.com/jobs/view/123",
            apply_url="https://example.com/apply",
            experience_level="Mid-Senior Level",
            skills=["Python", "PostgreSQL"],
        )
    ]

    saved = await save_linkedin_jobs(jobs, db=db)

    assert saved == 1
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_cookie_export_fields_are_normalized() -> None:
    context = AsyncMock()
    scraper = LinkedInScraper(
        [
            {
                "name": "li_at",
                "value": "secret",
                "sameSite": "no_restriction",
                "expirationDate": 2_000_000_000,
                "storeId": "0",
            }
        ]
    )

    await scraper._add_cookies(context)

    context.add_cookies.assert_awaited_once_with(
        [
            {
                "name": "li_at",
                "value": "secret",
                "sameSite": "None",
                "domain": ".linkedin.com",
                "path": "/",
                "expires": 2_000_000_000,
            }
        ]
    )


def test_load_naukri_cookies() -> None:
    assert load_naukri_cookies('[{"name": "naukriToken", "value": "secret"}]') == [
        {"name": "naukriToken", "value": "secret"}
    ]


def test_load_bayt_cookies() -> None:
    assert load_bayt_cookies('[{"name": "baytToken", "value": "secret"}]') == [
        {"name": "baytToken", "value": "secret"}
    ]


def test_source_login_urls() -> None:
    naukri = NaukriScraper([{"name": "a", "value": "b"}])
    bayt = BaytScraper([{"name": "a", "value": "b"}])

    assert naukri.login_url == "https://www.naukri.com/"
    assert bayt.login_url == "https://www.bayt.com/"


def test_naukri_search_url_uses_seo_route() -> None:
    scraper = NaukriScraper([{"name": "a", "value": "b"}])
    url = scraper._search_url(
        SearchRequest(keywords="python backend", location="Delhi", max_jobs=25)
    )

    assert url.startswith("https://www.naukri.com/python-backend-jobs-in-delhi?")
    assert "k=python+backend" in url
    assert "l=Delhi" in url
    assert "nignbevent_src=jobsearchDeskGNB" in url
