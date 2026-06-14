import asyncio

from playwright.async_api import Locator, async_playwright

from app.core.config import settings
from app.modules.scrapers.base import LAUNCH_ARGS, STEALTH_INIT_SCRIPT, SearchRequest
from app.modules.scrapers.naukri import NaukriScraper, load_naukri_cookies


async def first_text(card: Locator, sel: str) -> str | None:
    loc = card.locator(sel).first
    if await loc.count():
        t = (await loc.inner_text()).strip()
        return t or None
    return None


async def extract(card: Locator) -> dict:
    title_a = card.locator("a.title").first
    title = (await title_a.inner_text()).strip() if await title_a.count() else None
    href = await title_a.get_attribute("href") if await title_a.count() else None
    company = await first_text(card, "a.comp-name")
    exp = await first_text(card, ".exp-wrap .expwdth, .expwdth")
    sal = await first_text(card, ".sal-wrap span[title], .sal span")
    loc = await first_text(card, ".loc-wrap .locWdth, .locWdth")
    desc = await first_text(card, ".job-desc")
    skills = []
    tags = card.locator("ul.tags-gt li")
    for i in range(await tags.count()):
        skills.append((await tags.nth(i).inner_text()).strip())
    return {"title": title, "company": company, "exp": exp, "sal": sal,
            "loc": loc, "skills": skills, "url": href, "desc": (desc or "")[:60]}


async def main() -> None:
    cookies = load_naukri_cookies(settings.naukri_cookies_json)
    scraper = NaukriScraper(cookies, headless=False, user_agent=settings.scraper_user_agent)
    search = SearchRequest(keywords="python developer", location="Delhi", max_jobs=25)
    base_url = scraper._search_url(search)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=LAUNCH_ARGS)
        ctx = await browser.new_context(
            locale="en-US", user_agent=scraper.user_agent, timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)
        await scraper._add_cookies(ctx)
        page = await ctx.new_page()

        all_jobs = []
        for page_no in (1, 2):
            # path-suffix pagination scheme: ...-jobs-in-delhi-2?...
            if page_no == 1:
                url = base_url
            else:
                path, _, qs = base_url.partition("?")
                url = f"{path}-{page_no}?{qs}"
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await page.locator("div.cust-job-tuple").first.wait_for(state="visible", timeout=20000)
            except Exception:
                print(f"page {page_no}: no cards (url={url})")
                break
            await asyncio.sleep(2)
            cards = page.locator("div.srp-jobtuple-wrapper")
            n = await cards.count()
            print(f"page {page_no}: {n} cards, url={url}")
            for i in range(n):
                all_jobs.append(await extract(cards.nth(i)))

        print("TOTAL EXTRACTED:", len(all_jobs))
        for j in all_jobs[:3]:
            print(j)
        # integrity check
        ok = sum(1 for j in all_jobs if j["title"] and j["company"] and j["url"])
        print(f"WITH title+company+url: {ok}/{len(all_jobs)}")
        await browser.close()


asyncio.run(main())
