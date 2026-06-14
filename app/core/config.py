from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    name: str = "AI Job Agent"
    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_agent"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    openai_api_key: str | None = None
    openai_matching_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_request_timeout_seconds: float = 60.0

    scheduled_scrape_keywords: str = "python developer"
    scheduled_scrape_location: str = "remote"
    scheduled_scrape_max_jobs: int = 25
    scheduled_scrape_sources: list[str] = Field(
        default_factory=lambda: ["linkedin", "naukri", "bayt", "indeed"]
    )
    scheduled_scrape_hour: int = 8
    scheduled_scrape_minute: int = 0

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str | None = None
    smtp_timeout_seconds: float = 30.0

    linkedin_cookies_json: str = "[]"
    naukri_cookies_json: str = "[]"
    bayt_cookies_json: str = "[]"
    indeed_cookies_json: str = "[]"
    linkedin_headless: bool = True
    naukri_headless: bool = True
    bayt_headless: bool = True
    indeed_headless: bool = True
    scraper_delay_min_seconds: float = 1.5
    scraper_delay_max_seconds: float = 3.5
    scraper_navigation_timeout_ms: int = 30_000
    scraper_user_agent: str | None = None
    scraper_proxy_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
