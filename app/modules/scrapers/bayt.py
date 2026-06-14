from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from playwright.async_api import Locator, Page

from app.core.config import settings
from app.modules.scrapers.base import (
    PlaywrightJobScraper,
    ScrapedJob,
    SearchRequest,
    load_cookies,
)

logger = logging.getLogger(__name__)

JOB_CARD = "article.job-card, div.job-card"
TITLE_SELECTORS = (
    "h1",
    ".job-title",
    ".card-title",
)
COMPANY_SELECTORS = (
    ".company-name",
    ".job-company",
)
LOCATION_SELECTORS = (
    ".job-location",
    ".location",
)
DESCRIPTION_SELECTORS = (
    ".job-description",
    "#job-description",
    ".description",
)
APPLY_SELECTORS = (
    "a[href*='apply']",
    "a.btn-apply",
)
EXPERIENCE_SELECTORS = (
    ".experience",
    ".job-experience",
)
SKILL_SELECTORS = (
    ".skills li",
    ".job-skills li",
    ".tags li",
)


@dataclass(slots=True)
class BaytJob(ScrapedJob):
    pass


class BaytScraper(PlaywrightJobScraper):
    source_name = "bayt"

    def __init__(self, cookies: list[dict[str, Any]], **kwargs: Any) -> None:
        super().__init__(cookies, cookie_domain=".bayt.com", **kwargs)

    @property
    def login_url(self) -> str:
        return "https://www.bayt.com/"

    @property
    def job_card_selector(self) -> str:
        return JOB_CARD

    @property
    def login_failure_markers(self) -> tuple[str, ...]:
        return ("login", "sign-in")

    async def _open_search(self, page: Page, search: SearchRequest) -> None:
        query = urlencode({"q": search.keywords, "location": search.location})
        await page.goto(f"https://www.bayt.com/en/uae/jobs/?{query}", wait_until="domcontentloaded")
        await page.locator(JOB_CARD).first.wait_for(state="visible")
        await self._delay()

    async def _card_url(self, card: Locator) -> str | None:
        link = card.locator("a[href*='/en/']").first
        href = await link.get_attribute("href")
        if not href:
            return None
        return href if href.startswith("http") else f"https://www.bayt.com{href}"

    async def _extract_job(self, page: Page, source_url: str) -> BaytJob | None:
        title = await self._first_text(page, TITLE_SELECTORS)
        company = await self._first_text(page, COMPANY_SELECTORS)
        if not title or not company:
            logger.warning("bayt_job_skipped", extra={"source_url": source_url})
            return None
        description = await self._first_text(page, DESCRIPTION_SELECTORS)
        experience_text = " ".join(await self._all_text(page, EXPERIENCE_SELECTORS))
        skills = await self._all_text(page, SKILL_SELECTORS)
        return BaytJob(
            title=title,
            company=company,
            source_url=source_url,
            location=await self._first_text(page, LOCATION_SELECTORS),
            description=description,
            apply_url=await self._first_href(page, APPLY_SELECTORS) or source_url,
            experience_level=self._extract_experience_level(experience_text)
            or self._extract_experience_level(description),
            skills=self._clean_skills(skills) or self._extract_skills(description),
        )


def load_bayt_cookies(raw_json: str) -> list[dict[str, Any]]:
    return load_cookies(raw_json, source_name="bayt")


async def scrape_and_save_bayt_jobs(keywords: str, location: str, max_jobs: int) -> int:
    scraper = BaytScraper(
        load_bayt_cookies(settings.bayt_cookies_json),
        headless=settings.bayt_headless,
        delay_min_seconds=settings.scraper_delay_min_seconds,
        delay_max_seconds=settings.scraper_delay_max_seconds,
        navigation_timeout_ms=settings.scraper_navigation_timeout_ms,
        user_agent=settings.scraper_user_agent,
        proxy_url=settings.scraper_proxy_url,
    )
    jobs = await scraper.scrape(
        SearchRequest(keywords=keywords, location=location, max_jobs=max_jobs)
    )
    return await scraper.save_jobs(jobs)
