from fastapi import APIRouter, status

from app.modules.common import task_response
from app.modules.scrapers.schemas import LinkedInScrapeRequest, ScrapeRequest, TaskQueued
from app.modules.scrapers.tasks import (
    scrape_bayt_jobs,
    scrape_indeed_jobs,
    scrape_jobs,
    scrape_linkedin_jobs,
    scrape_naukri_jobs,
)

router = APIRouter()


@router.post("/runs", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_scrape(payload: ScrapeRequest) -> dict[str, str]:
    task = scrape_jobs.delay(payload.source, str(payload.url))
    return task_response(task)


@router.post("/linkedin/runs", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_linkedin_scrape(payload: LinkedInScrapeRequest) -> dict[str, str]:
    task = scrape_linkedin_jobs.delay(payload.keywords, payload.location, payload.max_jobs)
    return task_response(task)


@router.post("/naukri/runs", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_naukri_scrape(payload: LinkedInScrapeRequest) -> dict[str, str]:
    task = scrape_naukri_jobs.delay(payload.keywords, payload.location, payload.max_jobs)
    return task_response(task)


@router.post("/bayt/runs", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_bayt_scrape(payload: LinkedInScrapeRequest) -> dict[str, str]:
    task = scrape_bayt_jobs.delay(payload.keywords, payload.location, payload.max_jobs)
    return task_response(task)


@router.post("/indeed/runs", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_indeed_scrape(payload: LinkedInScrapeRequest) -> dict[str, str]:
    task = scrape_indeed_jobs.delay(payload.keywords, payload.location, payload.max_jobs)
    return task_response(task)
