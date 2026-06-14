from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import (
    BrowserContext,
    Locator,
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.modules.jobs.model import Job

logger = logging.getLogger(__name__)

PLAYWRIGHT_COOKIE_FIELDS = {
    "name",
    "value",
    "url",
    "domain",
    "path",
    "expires",
    "httpOnly",
    "secure",
    "sameSite",
    "partitionKey",
}

# Only used to mask the "HeadlessChrome" token in headless mode. Headed browsers keep
# their native UA: a spoofed OS/version contradicts navigator.platform and the real
# engine fingerprint, which bot detection (e.g. Akamai) can cross-check.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Flags that remove the most common automation tells from the launched browser.
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# Runs before any page script; masks the properties bot-detection JS checks first.
STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || { runtime: {} };
"""


@dataclass(slots=True)
class ScrapedJob:
    title: str
    company: str
    source_url: str
    location: str | None = None
    description: str | None = None
    apply_url: str | None = None
    experience_level: str | None = None
    experience_min_years: float | None = None
    experience_max_years: float | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    skills: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SearchRequest:
    keywords: str
    location: str
    max_jobs: int = 25


class PlaywrightJobScraper(ABC):
    source_name: str

    def __init__(
        self,
        cookies: list[dict[str, Any]],
        *,
        headless: bool = True,
        delay_min_seconds: float = 1.5,
        delay_max_seconds: float = 3.5,
        navigation_timeout_ms: int = 30_000,
        cookie_domain: str,
        locale: str = "en-US",
        user_agent: str | None = None,
        timezone_id: str = "Asia/Kolkata",
        proxy_url: str | None = None,
    ) -> None:
        # Cookies are optional: public search pages (Naukri, Indeed, Bayt) scrape fine
        # without a session. Login-gated flows fail later in `_verify_login` instead.
        if delay_min_seconds < 0 or delay_max_seconds < delay_min_seconds:
            raise ValueError("Invalid scraper delay range")

        self.cookies = cookies
        self.headless = headless
        self.delay_min_seconds = delay_min_seconds
        self.delay_max_seconds = delay_max_seconds
        self.navigation_timeout_ms = navigation_timeout_ms
        self.cookie_domain = cookie_domain
        self.locale = locale
        self.user_agent = user_agent or (DEFAULT_USER_AGENT if headless else None)
        self.timezone_id = timezone_id
        self.proxy_url = proxy_url

    async def scrape(self, search: SearchRequest) -> list[ScrapedJob]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=LAUNCH_ARGS,
                proxy={"server": self.proxy_url} if self.proxy_url else None,
            )
            context_kwargs: dict[str, Any] = {
                "locale": self.locale,
                "timezone_id": self.timezone_id,
                "viewport": {"width": 1366, "height": 768},
                # extra_http_headers are attached to EVERY request, XHR/fetch included.
                # Never add navigation-only headers (e.g. Upgrade-Insecure-Requests) here:
                # real browsers omit them on XHR, so Akamai flags the session and serves
                # an empty shell page. Chromium already sends them on navigations itself.
                "extra_http_headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                },
            }
            if self.user_agent:
                context_kwargs["user_agent"] = self.user_agent
            context = await browser.new_context(**context_kwargs)
            context.set_default_timeout(self.navigation_timeout_ms)
            await context.add_init_script(STEALTH_INIT_SCRIPT)
            await self._add_cookies(context)
            page = await context.new_page()
            try:
                await self._verify_login(page)
                await self._open_search(page, search)
                return await self._collect_jobs(page, search.max_jobs)
            finally:
                await context.close()
                await browser.close()

    async def _add_cookies(self, context: BrowserContext) -> None:
        cookies = []
        for cookie in self.cookies:
            normalized = {
                key: value for key, value in cookie.items() if key in PLAYWRIGHT_COOKIE_FIELDS
            }
            normalized.setdefault("domain", self.cookie_domain)
            normalized.setdefault("path", "/")
            if normalized.get("sameSite") == "no_restriction":
                normalized["sameSite"] = "None"
            elif normalized.get("sameSite") == "unspecified":
                normalized.pop("sameSite")
            elif isinstance(normalized.get("sameSite"), str):
                normalized["sameSite"] = normalized["sameSite"].title()
            if "expirationDate" in cookie and "expires" not in normalized:
                normalized["expires"] = cookie["expirationDate"]
            cookies.append(normalized)
        await context.add_cookies(cookies)

    async def _verify_login(self, page: Page) -> None:
        await page.goto(self.login_url, wait_until="domcontentloaded")
        await self._delay()
        if any(marker in page.url for marker in self.login_failure_markers):
            raise RuntimeError(f"{self.source_name} cookies are expired or require verification")

    async def _delay(self) -> None:
        await asyncio.sleep(random.uniform(self.delay_min_seconds, self.delay_max_seconds))

    async def _first_text(self, page: Page, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            locator = page.locator(selector).first
            if await locator.count():
                text = (await locator.inner_text()).strip()
                if text:
                    return text
        return None

    async def _first_href(self, page: Page, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            locator = page.locator(selector).first
            if await locator.count():
                href = await locator.get_attribute("href")
                if href:
                    return href
        return None

    async def _root_first_text(self, root: Locator, selectors: tuple[str, ...]) -> str | None:
        """Like `_first_text`, but scoped to a container element (e.g. a job card)."""
        for selector in selectors:
            locator = root.locator(selector).first
            if await locator.count():
                text = (await locator.inner_text()).strip()
                if text:
                    return text
        return None

    async def _root_all_text(self, root: Locator, selectors: tuple[str, ...]) -> list[str]:
        values: list[str] = []
        for selector in selectors:
            locator = root.locator(selector)
            for index in range(await locator.count()):
                text = (await locator.nth(index).inner_text()).strip()
                if text:
                    values.append(text)
        return values

    async def _all_text(self, page: Page, selectors: tuple[str, ...]) -> list[str]:
        values: list[str] = []
        for selector in selectors:
            locator = page.locator(selector)
            for index in range(await locator.count()):
                text = (await locator.nth(index).inner_text()).strip()
                if text:
                    values.append(text)
        return values

    @staticmethod
    def _extract_experience_level(text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(
            (
                r"\b("
                r"internship|entry level|associate|mid-senior level|director|"
                r"executive|fresher|trainee|junior|senior"
                r")\b"
            ),
            text,
            re.IGNORECASE,
        )
        return match.group(1).title() if match else None

    @staticmethod
    def _extract_skills(text: str | None) -> list[str]:
        if not text:
            return []
        match = re.search(
            r"(?:required|preferred|technical|core)\s+skills?\s*:?\s*(.+?)(?:\n\n|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return []
        return PlaywrightJobScraper._clean_skills(re.split(r"[,;\n•]", match.group(1)))

    @staticmethod
    def _clean_skills(values: list[str]) -> list[str]:
        cleaned = [value.strip(" .-/") for value in values if 1 < len(value.strip(" .-/")) <= 100]
        return list(dict.fromkeys(cleaned))[:25]

    @staticmethod
    def normalize_source_url(source_url: str, *, prefix: str | None = None) -> str:
        if source_url.startswith("http"):
            return source_url
        if not prefix:
            raise ValueError("prefix is required for relative source URLs")
        return f"{prefix}{source_url}"

    async def _collect_jobs(self, page: Page, max_jobs: int) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        seen_urls: set[str] = set()
        previous_count = 0
        while len(jobs) < max_jobs:
            cards = page.locator(self.job_card_selector)
            card_count = await cards.count()
            if card_count == 0:
                break
            for index in range(card_count):
                if len(jobs) >= max_jobs:
                    break
                card = cards.nth(index)
                source_url = await self._card_url(card)
                if not source_url or source_url in seen_urls:
                    continue
                seen_urls.add(source_url)
                await self._open_card(card)
                await self._delay()
                job = await self._extract_job(page, source_url)
                if job is not None:
                    jobs.append(job)
            if len(jobs) >= max_jobs:
                break
            await self._scroll_for_more(page)
            await self._delay()
            new_count = await page.locator(self.job_card_selector).count()
            if new_count <= previous_count:
                break
            previous_count = new_count
        return jobs

    async def _wait_for_job_cards(self, page: Page, retries: int = 2) -> None:
        """Wait for job cards to render.

        These sites are client-rendered SPAs: the document reaches
        ``domcontentloaded`` before job cards are painted, and the first render
        intermittently stalls in a loading state. A reload reliably recovers it,
        so we retry before giving up; on final failure we log what actually
        loaded so a real block is distinguishable from a slow render.
        """
        for attempt in range(retries + 1):
            try:
                await page.locator(self.job_card_selector).first.wait_for(state="visible")
                return
            except PlaywrightTimeoutError:
                if attempt < retries:
                    # Back off (longer each attempt) to let rate limits ease, then reload —
                    # a fresh request usually returns a fully rendered page.
                    await asyncio.sleep(self.delay_max_seconds * (attempt + 2))
                    await page.reload(wait_until="domcontentloaded")
                    continue
                title = await page.title()
                body = await self._first_text(page, ("body",)) or ""
                logger.error(
                    "%s_results_not_found",
                    self.source_name,
                    extra={
                        "url": page.url,
                        "page_title": title,
                        "body_excerpt": body[:600],
                        "selector": self.job_card_selector,
                    },
                )
                raise

    async def _scroll_for_more(self, page: Page) -> None:
        await page.locator(self.job_card_selector).last.scroll_into_view_if_needed()

    async def _open_card(self, card: Locator) -> None:
        await card.scroll_into_view_if_needed()
        await card.click()

    @classmethod
    async def persist_jobs(
        cls, source_name: str, jobs: list[ScrapedJob], db: AsyncSession | None = None
    ) -> int:
        if not jobs:
            return 0

        values = [
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "source": source_name,
                "source_url": job.source_url,
                "apply_url": job.apply_url,
                "description": job.description,
                "experience_level": job.experience_level,
                "experience_min_years": job.experience_min_years,
                "experience_max_years": job.experience_max_years,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_currency": job.salary_currency,
                "skills": job.skills,
                "status": "discovered",
            }
            for job in jobs
        ]
        statement = insert(Job).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=[Job.source_url],
            set_={
                "title": statement.excluded.title,
                "company": statement.excluded.company,
                "location": statement.excluded.location,
                "apply_url": statement.excluded.apply_url,
                "description": statement.excluded.description,
                "experience_level": statement.excluded.experience_level,
                "experience_min_years": statement.excluded.experience_min_years,
                "experience_max_years": statement.excluded.experience_max_years,
                "salary_min": statement.excluded.salary_min,
                "salary_max": statement.excluded.salary_max,
                "salary_currency": statement.excluded.salary_currency,
                "skills": statement.excluded.skills,
            },
        )
        if db is None:
            async with SessionLocal() as session:
                await session.execute(statement)
                await session.commit()
        else:
            await db.execute(statement)
            await db.commit()
        return len(values)

    async def save_jobs(self, jobs: list[ScrapedJob], db: AsyncSession | None = None) -> int:
        return await self.persist_jobs(self.source_name, jobs, db=db)

    @property
    @abstractmethod
    def login_url(self) -> str:
        pass

    @property
    @abstractmethod
    def job_card_selector(self) -> str:
        pass

    @property
    @abstractmethod
    def login_failure_markers(self) -> tuple[str, ...]:
        pass

    @abstractmethod
    async def _open_search(self, page: Page, search: SearchRequest) -> None:
        pass

    @abstractmethod
    async def _card_url(self, card: Locator) -> str | None:
        pass

    @abstractmethod
    async def _extract_job(self, page: Page, source_url: str) -> ScrapedJob | None:
        pass


def load_cookies(raw_json: str, *, source_name: str) -> list[dict[str, Any]]:
    try:
        cookies = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"APP_{source_name.upper()}_COOKIES_JSON must contain valid JSON") from exc
    if not isinstance(cookies, list) or not all(isinstance(cookie, dict) for cookie in cookies):
        raise ValueError(
            f"APP_{source_name.upper()}_COOKIES_JSON must be a JSON array of cookie objects"
        )
    return cookies
