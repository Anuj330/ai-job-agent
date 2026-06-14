from pydantic import BaseModel, Field, HttpUrl


class ScrapeRequest(BaseModel):
    source: str
    url: HttpUrl


class TaskQueued(BaseModel):
    task_id: str
    status: str


class LinkedInScrapeRequest(BaseModel):
    keywords: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    max_jobs: int = Field(default=25, ge=1, le=100)


JobSearchRequest = LinkedInScrapeRequest
