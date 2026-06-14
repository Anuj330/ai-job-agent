"""Probe Akamai block triggers: UA override x cookie set, direct search loads only."""
import asyncio

from playwright.async_api import async_playwright

from app.core.config import settings
from app.modules.scrapers.base import LAUNCH_ARGS, STEALTH_INIT_SCRIPT
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies

SEARCH = "https://www.naukri.com/python-developer-jobs-in-delhi?k=python+developer&l=Delhi"
AKAMAI = {"bm_sv", "bm_mi", "ak_bmsc", "_abck", "bm_sz"}
ANALYTICS = {"_ga", "_gcl_au", "__gpi", "__gads", "__eoi", "_t_ds", "jd"}


def cookie_sets() -> dict[str, list[dict]]:
    full = load_naukri_cookies(settings.naukri_cookies_json)
    auth_only = [c for c in full if c["name"] not in AKAMAI | ANALYTICS and not c["name"].startswith("_ga")]
    return {"none": [], "auth-only": auth_only, "full": full}


async def run(pw, ua_override: bool, cookie_label: str, cookies: list[dict]) -> None:
    browser = await pw.chromium.launch(headless=False, args=LAUNCH_ARGS)
    kwargs = dict(
        locale="en-US", timezone_id="Asia/Kolkata",
        viewport={"width": 1366, "height": 768},
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    if ua_override:
        kwargs["user_agent"] = settings.scraper_user_agent or None
    ctx = await browser.new_context(**{k: v for k, v in kwargs.items() if v is not None})
    await ctx.add_init_script(STEALTH_INIT_SCRIPT)
    if cookies:
        scraper = NaukriScraper(cookies, headless=False)
        await scraper._add_cookies(ctx)
    page = await ctx.new_page()
    real_ua = await page.evaluate("navigator.userAgent")
    await page.goto(SEARCH, wait_until="domcontentloaded")
    await asyncio.sleep(6)
    html = await page.content()
    cards = await page.locator("div.cust-job-tuple").count()
    print(
        f"ua_override={ua_override} cookies={cookie_label:9s} "
        f"len={len(html):7d} cards={cards:2d} title={(await page.title())[:40]!r} ua={real_ua[:60]!r}",
        flush=True,
    )
    await browser.close()


async def main() -> None:
    sets = cookie_sets()
    async with async_playwright() as pw:
        for ua_override in (False, True):
            for label, cookies in sets.items():
                try:
                    await run(pw, ua_override, label, cookies)
                except Exception as exc:
                    print(f"ua_override={ua_override} cookies={label}: FAILED {exc}", flush=True)
                await asyncio.sleep(4)


asyncio.run(main())
