import asyncio

from playwright.async_api import async_playwright

from app.core.config import settings
from app.modules.scrapers.base import LAUNCH_ARGS, STEALTH_INIT_SCRIPT, SearchRequest
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies


async def run(label: str, visit_home: bool) -> None:
    cookies = load_naukri_cookies(settings.naukri_cookies_json)
    scraper = NaukriScraper(cookies, headless=False, user_agent=settings.scraper_user_agent)
    search = SearchRequest(keywords="python developer", location="Delhi", max_jobs=25)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=LAUNCH_ARGS)
        ctx = await browser.new_context(
            locale="en-US", user_agent=scraper.user_agent, timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9", "Upgrade-Insecure-Requests": "1"},
        )
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)
        await scraper._add_cookies(ctx)
        page = await ctx.new_page()
        if visit_home:
            await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2.5)
            print(f"[{label}] HOME title={ (await page.title())!r}")
        await page.goto(scraper._search_url(search), wait_until="domcontentloaded")
        await asyncio.sleep(3)
        title = await page.title()
        html = await page.content()
        cards = await page.locator("div.cust-job-tuple").count()
        print(f"[{label}] SEARCH title={title!r} len={len(html)} denied={'access denied' in html.lower()} cards={cards}")
        await browser.close()


async def main() -> None:
    await run("WITH homepage first (production flow)", True)
    await run("DIRECT to search (probe flow)", False)


asyncio.run(main())
