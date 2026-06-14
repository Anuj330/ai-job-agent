.PHONY: install run worker migrate test lint compose-up compose-down

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.core.celery_app.celery_app worker --loglevel=INFO

migrate:
	alembic upgrade head

test:
	pytest

lint:
	ruff check .

compose-up:
	docker compose up --build

compose-down:
	docker compose down

