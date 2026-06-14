from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.config import settings
from app.modules.scrapers.base import (
    PlaywrightJobScraper,
    ScrapedJob,
    SearchRequest,
    load_cookies,
)

logger = logging.getLogger(__name__)

# Naukri renders all listing data inside each search-results card, so we parse the
# card directly instead of opening each job's detail page.
JOB_CARD = "div.srp-jobtuple-wrapper, div.cust-job-tuple"
CARD_TITLE_SELECTORS = ("a.title",)
CARD_COMPANY_SELECTORS = ("a.comp-name", ".comp-name")
CARD_LOCATION_SELECTORS = (".loc-wrap .locWdth", ".loc-wrap span[title]", ".locWdth")
CARD_EXPERIENCE_SELECTORS = (".exp-wrap .expwdth", ".exp-wrap span[title]", ".expwdth")
CARD_SALARY_SELECTORS = (".sal-wrap span[title]", ".sal-wrap .sal", ".sal span")
CARD_DESCRIPTION_SELECTORS = (".job-desc",)

# Naukri quotes annual pay in Indian units: "Lakh"/"Lac" = 1e5, "Cr"/"Crore" = 1e7.
_SALARY_MULTIPLIERS = (
    ("cr", 10_000_000.0),
    ("lakh", 100_000.0),
    ("lac", 100_000.0),
    ("lpa", 100_000.0),
)
CARD_SKILL_SELECTORS = ("ul.tags-gt li", ".tags-gt li")


@dataclass(slots=True)
class NaukriJob(ScrapedJob):
    pass


class NaukriScraper(PlaywrightJobScraper):
    source_name = "naukri"
    _base_search_url: str = ""

    def __init__(self, cookies: list[dict[str, Any]], **kwargs: Any) -> None:
        super().__init__(cookies, cookie_domain=".naukri.com", **kwargs)

    @property
    def login_url(self) -> str:
        return "https://www.naukri.com/"

    @property
    def job_card_selector(self) -> str:
        return JOB_CARD

    @property
    def login_failure_markers(self) -> tuple[str, ...]:
        return ("login", "auth")

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "jobs"

    @staticmethod
    def _parse_experience(text: str | None) -> tuple[float | None, float | None]:
        """Parse Naukri's "0-5 Yrs" / "5+ Yrs" card text into (min, max) years.

        Requires a year token so stray values (e.g. a posting date like "13 Jun"
        that the experience selector occasionally matches) parse to (None, None).
        """
        if not text or "yr" not in text.lower():
            return None, None
        bounds = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
        if bounds:
            return float(bounds.group(1)), float(bounds.group(2))
        single = re.search(r"(\d+(?:\.\d+)?)", text)
        if single:
            value = float(single.group(1))
            return value, None if "+" in text else value
        return None, None

    @staticmethod
    def _parse_salary(text: str | None) -> tuple[float | None, float | None, str | None]:
        """Parse Naukri pay text (e.g. "4-6.5 Lacs PA") into (min, max, currency).

        Returns all-None when pay is hidden ("Not disclosed") or unparseable.
        """
        if not text:
            return None, None, None
        lowered = text.lower()
        if "disclos" in lowered:
            return None, None, None
        multiplier = next((m for token, m in _SALARY_MULTIPLIERS if token in lowered), 1.0)
        numbers = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
        if not numbers:
            return None, None, None
        values = sorted(float(n) * multiplier for n in numbers[:2])
        low, high = (values[0], values[-1])
        return low, high, "INR"

    def _search_url(self, search: SearchRequest) -> str:
        route_keyword = self._slugify(search.keywords)
        route_location = self._slugify(search.location)
        query = urlencode(
            {
                "k": search.keywords,
                "l": search.location,
                "nignbevent_src": "jobsearchDeskGNB",
            }
        )
        return f"https://www.naukri.com/{route_keyword}-jobs-in-{route_location}?{query}"

    def _page_url(self, page_no: int) -> str:
        """Naukri paginates via a `-N` suffix on the SEO path (page 1 has no suffix)."""
        if page_no <= 1:
            return self._base_search_url
        path, _, query = self._base_search_url.partition("?")
        return f"{path}-{page_no}?{query}" if query else f"{path}-{page_no}"

    async def _open_search(self, page: Page, search: SearchRequest) -> None:
        self._base_search_url = self._search_url(search)
        await page.goto(self._base_search_url, wait_until="domcontentloaded")
        await self._wait_for_job_cards(page)
        await self._delay()

    async def _collect_jobs(self, page: Page, max_jobs: int) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        seen_urls: set[str] = set()
        page_no = 1
        while len(jobs) < max_jobs:
            cards = page.locator(self.job_card_selector)
            card_count = await cards.count()
            if card_count == 0:
                break
            for index in range(card_count):
                if len(jobs) >= max_jobs:
                    break
                job = await self._extract_card(cards.nth(index))
                if job is None or job.source_url in seen_urls:
                    continue
                seen_urls.add(job.source_url)
                jobs.append(job)
            if len(jobs) >= max_jobs:
                break
            page_no += 1
            await page.goto(self._page_url(page_no), wait_until="domcontentloaded")
            try:
                await self._wait_for_job_cards(page)
            except PlaywrightTimeoutError:
                break
            await self._delay()
        return jobs

    async def _extract_card(self, card: Locator) -> NaukriJob | None:
        title_link = card.locator(CARD_TITLE_SELECTORS[0]).first
        if not await title_link.count():
            return None
        title = (await title_link.inner_text()).strip()
        source_url = await title_link.get_attribute("href")
        company = await self._root_first_text(card, CARD_COMPANY_SELECTORS)
        if not title or not company or not source_url:
            logger.warning("naukri_card_skipped", extra={"source_url": source_url})
            return None
        if not source_url.startswith("http"):
            source_url = f"https://www.naukri.com{source_url}"
        description = await self._root_first_text(card, CARD_DESCRIPTION_SELECTORS)
        experience = await self._root_first_text(card, CARD_EXPERIENCE_SELECTORS)
        salary = await self._root_first_text(card, CARD_SALARY_SELECTORS)
        skills = await self._root_all_text(card, CARD_SKILL_SELECTORS)
        exp_min, exp_max = self._parse_experience(experience)
        salary_min, salary_max, salary_currency = self._parse_salary(salary)
        return NaukriJob(
            title=title,
            company=company,
            source_url=source_url,
            location=await self._root_first_text(card, CARD_LOCATION_SELECTORS),
            description=description,
            apply_url=source_url,
            experience_level=experience or self._extract_experience_level(description),
            experience_min_years=exp_min,
            experience_max_years=exp_max,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            skills=self._clean_skills(skills) or self._extract_skills(description),
        )

    # Retained to satisfy the abstract base; Naukri parses cards in-place above.
    async def _card_url(self, card: Locator) -> str | None:
        return await self._root_first_text(card, CARD_TITLE_SELECTORS)

    async def _extract_job(self, page: Page, source_url: str) -> NaukriJob | None:
        return None


def load_naukri_cookies(raw_json: str) -> list[dict[str, Any]]:
    return load_cookies(raw_json, source_name="naukri")


async def scrape_and_save_naukri_jobs(keywords: str, location: str, max_jobs: int) -> int:
    scraper = NaukriScraper(
        load_naukri_cookies(settings.naukri_cookies_json),
        headless=settings.naukri_headless,
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
