from __future__ import annotations

import logging
import re
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

JOB_CARD = "li.jobs-search-results__list-item, li.scaffold-layout__list-item"
TITLE_SELECTORS = (
    ".job-details-jobs-unified-top-card__job-title",
    ".jobs-unified-top-card__job-title",
    "h1",
)
COMPANY_SELECTORS = (
    ".job-details-jobs-unified-top-card__company-name",
    ".jobs-unified-top-card__company-name",
)
LOCATION_SELECTORS = (
    ".job-details-jobs-unified-top-card__tertiary-description-container span",
    ".jobs-unified-top-card__bullet",
)
DESCRIPTION_SELECTORS = ("#job-details", ".jobs-description__content")
APPLY_SELECTORS = (
    ".jobs-apply-button--top-card a",
    ".jobs-apply-button a",
    "a.jobs-apply-button",
)
EXPERIENCE_SELECTORS = (
    ".job-details-jobs-unified-top-card__job-insight span",
    ".jobs-unified-top-card__job-insight span",
)
SKILL_SELECTORS = (
    ".job-details-skill-match-status-list li",
    ".job-details-how-you-match__skills-item-subtitle",
)


@dataclass(slots=True)
class LinkedInJob(ScrapedJob):
    pass


class LinkedInScraper(PlaywrightJobScraper):
    source_name = "linkedin"

    def __init__(self, cookies: list[dict[str, Any]], **kwargs: Any) -> None:
        super().__init__(cookies, cookie_domain=".linkedin.com", **kwargs)

    @property
    def login_url(self) -> str:
        return "https://www.linkedin.com/feed/"

    @property
    def job_card_selector(self) -> str:
        return JOB_CARD

    @property
    def login_failure_markers(self) -> tuple[str, ...]:
        return ("login", "checkpoint")

    async def _open_search(self, page: Page, search: SearchRequest) -> None:
        query = urlencode({"keywords": search.keywords, "location": search.location})
        await page.goto(
            f"https://www.linkedin.com/jobs/search/?{query}",
            wait_until="domcontentloaded",
        )
        await page.locator(JOB_CARD).first.wait_for(state="visible")
        await self._delay()

    async def _card_url(self, card: Locator) -> str | None:
        link = card.locator("a[href*='/jobs/view/']").first
        href = await link.get_attribute("href")
        if not href:
            return None
        match = re.search(r"https?://[^?]+|/jobs/view/[^?]+", href)
        if not match:
            return None
        url = match.group(0)
        return url if url.startswith("http") else f"https://www.linkedin.com{url}"

    async def _extract_job(self, page: Page, source_url: str) -> LinkedInJob | None:
        title = await self._first_text(page, TITLE_SELECTORS)
        company = await self._first_text(page, COMPANY_SELECTORS)
        if not title or not company:
            logger.warning("linkedin_job_skipped", extra={"source_url": source_url})
            return None
        description = await self._first_text(page, DESCRIPTION_SELECTORS)
        experience_text = " ".join(await self._all_text(page, EXPERIENCE_SELECTORS))
        skills = await self._all_text(page, SKILL_SELECTORS)
        return LinkedInJob(
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


def load_linkedin_cookies(raw_json: str) -> list[dict[str, Any]]:
    return load_cookies(raw_json, source_name="linkedin")


async def save_linkedin_jobs(jobs: list[LinkedInJob], db: Any | None = None) -> int:
    return await LinkedInScraper.persist_jobs("linkedin", jobs, db=db)


async def scrape_and_save_linkedin_jobs(keywords: str, location: str, max_jobs: int) -> int:
    scraper = LinkedInScraper(
        load_linkedin_cookies(settings.linkedin_cookies_json),
        headless=settings.linkedin_headless,
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
