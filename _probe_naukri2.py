import asyncio

from playwright.async_api import async_playwright

from app.core.config import settings
from app.modules.scrapers.base import LAUNCH_ARGS, STEALTH_INIT_SCRIPT
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies

AKAMAI_COOKIE_NAMES = {"ak_bmsc", "bm_sv", "bm_mi", "bm_sz", "_abck"}


async def visit(label: str, cookies) -> None:
    scraper = NaukriScraper(
        [{"name": "x", "value": "y"}],  # constructor needs non-empty; we add real ones below
        headless=True,
        user_agent=settings.scraper_user_agent,
    )
    scraper.cookies = cookies if cookies else [{"name": "noop", "value": "1"}]
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
        if cookies:
            await scraper._add_cookies(ctx)
        page = await ctx.new_page()
        await page.goto("https://www.naukri.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        title = await page.title()
        html = await page.content()
        print(f"[{label}] TITLE={title!r} LEN={len(html)}")
        await browser.close()


async def main() -> None:
    all_cookies = load_naukri_cookies(settings.naukri_cookies_json)
    no_akamai = [c for c in all_cookies if c.get("name") not in AKAMAI_COOKIE_NAMES]
    print("total cookies:", len(all_cookies), "| without akamai:", len(no_akamai))

    await visit("A: no cookies at all", [])
    await visit("B: cookies minus akamai bm_*", no_akamai)
    await visit("C: all cookies (current behavior)", all_cookies)


asyncio.run(main())
