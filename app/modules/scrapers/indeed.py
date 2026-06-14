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

# Indeed renders rich data on each search-results card, so we parse cards directly
# (like Naukri) rather than opening each job's detail pane.
JOB_CARD = "div.job_seen_beacon, div[data-testid='slider_item']"
CARD_TITLE_SELECTORS = ("h2.jobTitle a", "a.jcs-JobTitle")
CARD_COMPANY_SELECTORS = ("[data-testid='company-name']", "span.companyName")
CARD_LOCATION_SELECTORS = ("[data-testid='text-location']", "div.companyLocation")
CARD_SALARY_SELECTORS = (
    "[data-testid='attribute_snippet_testid']",
    ".salary-snippet-container",
    ".metadata.salary-snippet-container",
)
CARD_DESCRIPTION_SELECTORS = ("[data-testid='jobsnippet_footer']", "div.job-snippet")

# Indeed quotes pay per period and across currencies; normalize to an annual figure.
_SALARY_PERIOD_MULTIPLIERS = (
    ("year", 1.0),
    ("annum", 1.0),
    ("yr", 1.0),
    ("month", 12.0),
    ("week", 52.0),
    ("day", 260.0),
    ("hour", 2080.0),
)
_SALARY_CURRENCIES = (
    ("₹", "INR"),
    ("rs", "INR"),
    ("$", "USD"),
    ("£", "GBP"),
    ("€", "EUR"),
    ("aed", "AED"),
)


@dataclass(slots=True)
class IndeedJob(ScrapedJob):
    pass


class IndeedScraper(PlaywrightJobScraper):
    source_name = "indeed"
    # Region host — defaults to the India site to match the product's primary market.
    base_host: str = "https://in.indeed.com"
    _search: SearchRequest | None = None

    def __init__(self, cookies: list[dict[str, Any]], **kwargs: Any) -> None:
        super().__init__(cookies, cookie_domain=".indeed.com", **kwargs)

    @property
    def login_url(self) -> str:
        return f"{self.base_host}/"

    @property
    def job_card_selector(self) -> str:
        return JOB_CARD

    @property
    def login_failure_markers(self) -> tuple[str, ...]:
        return ("account/login", "secure/login")

    @staticmethod
    def _parse_salary(text: str | None) -> tuple[float | None, float | None, str | None]:
        """Parse Indeed pay text (e.g. "₹50,000 - ₹80,000 a month") to annual (min, max, ccy)."""
        if not text:
            return None, None, None
        lowered = text.lower()
        numbers = [
            float(n.replace(",", ""))
            for n in re.findall(r"\d[\d,]*\.?\d*", text)
            if n.strip(",.")
        ]
        if not numbers:
            return None, None, None
        multiplier = next((m for token, m in _SALARY_PERIOD_MULTIPLIERS if token in lowered), 1.0)
        currency = next((code for token, code in _SALARY_CURRENCIES if token in lowered), None)
        values = sorted(n * multiplier for n in numbers[:2])
        return values[0], values[-1], currency

    def _search_url(self, search: SearchRequest, start: int = 0) -> str:
        params: dict[str, Any] = {"q": search.keywords, "l": search.location}
        if start:
            params["start"] = start
        return f"{self.base_host}/jobs?{urlencode(params)}"

    async def _open_search(self, page: Page, search: SearchRequest) -> None:
        self._search = search
        await page.goto(self._search_url(search), wait_until="domcontentloaded")
        await self._wait_for_job_cards(page)
        await self._delay()

    async def _collect_jobs(self, page: Page, max_jobs: int) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        seen_urls: set[str] = set()
        start = 0
        search = self._search
        if search is None:
            return jobs
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
            start += 10  # Indeed paginates 10 results per page via the `start` offset.
            await page.goto(self._search_url(search, start), wait_until="domcontentloaded")
            try:
                await self._wait_for_job_cards(page)
            except PlaywrightTimeoutError:
                break
            await self._delay()
        return jobs

    async def _extract_card(self, card: Locator) -> IndeedJob | None:
        title_link = card.locator(CARD_TITLE_SELECTORS[0]).first
        if not await title_link.count():
            title_link = card.locator(CARD_TITLE_SELECTORS[1]).first
        if not await title_link.count():
            return None
        title = (await title_link.inner_text()).strip()
        source_url = await title_link.get_attribute("href")
        company = await self._root_first_text(card, CARD_COMPANY_SELECTORS)
        if not title or not company or not source_url:
            logger.warning("indeed_card_skipped", extra={"source_url": source_url})
            return None
        if not source_url.startswith("http"):
            source_url = f"{self.base_host}{source_url}"
        description = await self._root_first_text(card, CARD_DESCRIPTION_SELECTORS)
        salary_min, salary_max, salary_currency = self._parse_salary(
            await self._root_first_text(card, CARD_SALARY_SELECTORS)
        )
        return IndeedJob(
            title=title,
            company=company,
            source_url=source_url,
            location=await self._root_first_text(card, CARD_LOCATION_SELECTORS),
            description=description,
            apply_url=source_url,
            experience_level=self._extract_experience_level(description),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            skills=self._extract_skills(description),
        )

    # Retained to satisfy the abstract base; Indeed parses cards in-place above.
    async def _card_url(self, card: Locator) -> str | None:
        return await self._root_first_text(card, CARD_TITLE_SELECTORS)

    async def _extract_job(self, page: Page, source_url: str) -> IndeedJob | None:
        return None


def load_indeed_cookies(raw_json: str) -> list[dict[str, Any]]:
    return load_cookies(raw_json, source_name="indeed")


async def scrape_and_save_indeed_jobs(keywords: str, location: str, max_jobs: int) -> int:
    scraper = IndeedScraper(
        load_indeed_cookies(settings.indeed_cookies_json),
        headless=settings.indeed_headless,
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
