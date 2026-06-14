# AI Job Agent Backend

Production-oriented FastAPI backend for job discovery, resume management, cover letters, and
asynchronous AI/scraper workflows.

## Stack

- FastAPI with modular routers
- PostgreSQL with async SQLAlchemy 2 and Alembic
- Redis for application caching/readiness and Celery transport
- Celery workers for scraper and AI jobs
- JSON application logs
- Docker Compose for local and production-like operation

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`, with OpenAPI docs at `/docs`.
If you also start the Next.js dashboard, it will be available at `http://localhost:3000`.

## Run locally

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Run a worker separately:

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
```

## Dashboard

The repository now includes a standalone Next.js dashboard in [`web/`](/home/tech/ai-job-agent/web).

Run it locally:

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

The dashboard expects the API at `NEXT_PUBLIC_API_BASE_URL` and uses a same-origin proxy for
browser-side match analysis requests.

## LinkedIn Scraper

Set `APP_LINKEDIN_COOKIES_JSON` to a JSON array of cookies exported from an authenticated LinkedIn
session. At minimum, this normally includes the `li_at` cookie. Treat this value as a secret.

Queue a search with:

```bash
curl -X POST http://localhost:8000/api/v1/scrapers/linkedin/runs \
  -H 'content-type: application/json' \
  -d '{"keywords":"Python backend","location":"United States","max_jobs":25}'
```

The Celery worker runs Chromium, applies bounded randomized pacing delays, extracts available job
details, and upserts results into PostgreSQL. Use scraping only where authorized and comply with the
site's terms and applicable law.

## Operations

- `GET /health/live`: process liveness
- `GET /health/ready`: PostgreSQL and Redis readiness
- `GET /docs`: API documentation
- `alembic upgrade head`: apply database migrations
- `pytest`: run tests
- `ruff check .`: run static checks

The scraper and AI Celery tasks intentionally define provider-neutral queue contracts. Add source
adapters and an LLM provider inside their respective module task implementations.
