from app.modules.scrapers.indeed import IndeedScraper


def test_parses_monthly_inr_to_annual() -> None:
    low, high, currency = IndeedScraper._parse_salary("₹50,000 - ₹80,000 a month")
    assert (low, high, currency) == (600_000.0, 960_000.0, "INR")


def test_parses_annual_usd() -> None:
    low, high, currency = IndeedScraper._parse_salary("$90,000 - $120,000 a year")
    assert (low, high, currency) == (90_000.0, 120_000.0, "USD")


def test_unparseable_salary_is_none() -> None:
    assert IndeedScraper._parse_salary("Full-time") == (None, None, None)
    assert IndeedScraper._parse_salary(None) == (None, None, None)
