import asyncio

from playwright.async_api import async_playwright

from app.core.config import settings
from app.modules.scrapers.base import (
    LAUNCH_ARGS,
    STEALTH_INIT_SCRIPT,
    SearchRequest,
)
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies


async def main() -> None:
    cookies = load_naukri_cookies(settings.naukri_cookies_json)
    scraper = NaukriScraper(
        cookies, headless=True, user_agent=settings.scraper_user_agent
    )
    search = SearchRequest(keywords="python developer", location="Delhi", max_jobs=25)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=LAUNCH_ARGS)
        ctx = await browser.new_context(
            locale="en-US",
            user_agent=scraper.user_agent,
            timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)
        await scraper._add_cookies(ctx)
        page = await ctx.new_page()

        await page.goto(scraper.login_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        print("HOME_URL:", page.url)
        print("HOME_TITLE:", await page.title())

        url = scraper._search_url(search)
        print("SEARCH_URL_REQUESTED:", url)
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(6)
        print("SEARCH_URL_FINAL:", page.url)
        print("SEARCH_TITLE:", await page.title())

        html = await page.content()
        with open("/tmp/naukri.html", "w") as fh:
            fh.write(html)
        print("HTML_LEN:", len(html))

        low = html.lower()
        for marker in [
            "access denied",
            "permission to access",
            "captcha",
            "unusual traffic",
            "verify you are human",
            "robot",
        ]:
            if marker in low:
                print("MARKER_FOUND:", marker)

        # Probe several candidate job-card selectors.
        for sel in [
            "div.srp-jobtuple-wrapper",
            "div.cust-job-tuple",
            "article.jobTuple",
            "div.jobTuple",
            "[data-job-id]",
            "a.title",
            "a[href*='/job-listings-']",
        ]:
            try:
                count = await page.locator(sel).count()
            except Exception as exc:  # noqa: BLE001
                count = f"err:{exc}"
            print(f"SELECTOR {sel!r}: {count}")

        await browser.close()


asyncio.run(main())
