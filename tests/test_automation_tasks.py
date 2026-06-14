from types import SimpleNamespace

import pytest

from app.core.celery_app import celery_app
from app.core.config import settings
from app.modules.ai.cover_letter_generation import CoverLetterGenerationResult
from app.modules.automation import tasks as automation_tasks


def test_beat_schedule_includes_scheduled_scraping() -> None:
    schedule = celery_app.conf.beat_schedule["scheduled-scraping"]

    assert schedule["task"] == "app.modules.automation.tasks.run_scheduled_scraping"
    assert schedule["kwargs"]["sources"] == ["linkedin", "naukri", "bayt"]


def test_run_scheduled_scraping_queues_each_source(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []

    def fake_delay(keywords: str, location: str, max_jobs: int) -> SimpleNamespace:
        queued.append(f"{keywords}:{location}:{max_jobs}")
        return SimpleNamespace(id=f"task-{len(queued)}")

    monkeypatch.setattr(automation_tasks.scrape_linkedin_jobs, "delay", fake_delay)
    monkeypatch.setattr(automation_tasks.scrape_naukri_jobs, "delay", fake_delay)
    monkeypatch.setattr(automation_tasks.scrape_bayt_jobs, "delay", fake_delay)

    result = automation_tasks.run_scheduled_scraping.run(
        keywords="python",
        location="remote",
        max_jobs=5,
        sources=["linkedin", "bayt"],
    )

    assert result["status"] == "queued"
    assert result["sources"] == ["linkedin", "bayt"]
    assert result["tasks"] == [
        {"source": "linkedin", "task_id": "task-1"},
        {"source": "bayt", "task_id": "task-2"},
    ]
    assert queued == ["python:remote:5", "python:remote:5"]


def test_run_ai_analysis_returns_match_result(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed = {
        "match_score": 81,
        "missing_skills": ["Docker"],
        "ats_keyword_recommendations": ["Kubernetes"],
        "resume_improvement_suggestions": ["Add impact metrics"],
        "interview_focus_areas": ["System design"],
    }

    class FakeMatchingService:
        async def analyze(self, payload):
            assert payload.resume_text.startswith("Experienced Python engineer")
            assert payload.job_description.startswith("We need a Python engineer")
            return SimpleNamespace(model_dump=lambda: parsed)

    monkeypatch.setattr(automation_tasks, "get_matching_service", lambda: FakeMatchingService())

    result = automation_tasks.run_ai_analysis.run(
        resume_text="Experienced Python engineer with SQL and APIs.",
        job_description="We need a Python engineer with SQL and system design skills.",
    )

    assert result == parsed


def test_generate_cover_letter_returns_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed = CoverLetterGenerationResult(
        cover_letter_markdown=(
            "Dear Hiring Team,\n\nI'm excited to apply.\n\nBest regards,\nCandidate"
        )
    )

    class FakeCoverLetterService:
        async def generate(self, payload):
            assert payload.tone == "startup"
            return parsed

    monkeypatch.setattr(
        automation_tasks,
        "get_cover_letter_generation_service",
        lambda: FakeCoverLetterService(),
    )

    result = automation_tasks.generate_cover_letter.run(
        resume_text="Experienced Python engineer with SQL, APIs, and product delivery.",
        job_description="We need a Python engineer who can work with SQL, APIs, and teams.",
        tone="startup",
    )

    assert result == parsed.model_dump()


def test_send_email_notification_uses_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            events.append(f"connect:{host}:{port}:{timeout}")

        def __enter__(self) -> "FakeSMTP":
            events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            events.append("exit")

        def starttls(self) -> None:
            events.append("tls")

        def login(self, username: str, password: str) -> None:
            events.append(f"login:{username}:{password}")

        def send_message(self, message) -> None:
            events.append(f"send:{message['To']}:{message['Subject']}")

    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "user@example.com")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_use_tls", True)
    monkeypatch.setattr(settings, "smtp_from_address", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_timeout_seconds", 12.0)
    monkeypatch.setattr(automation_tasks.smtplib, "SMTP", FakeSMTP)

    result = automation_tasks.send_email_notification.run(
        recipient_email="candidate@example.com",
        subject="Interview update",
        body="You have a new update.",
        content_type="plain",
    )

    assert result == {
        "status": "sent",
        "recipient_email": "candidate@example.com",
        "subject": "Interview update",
        "sender": "noreply@example.com",
    }
    assert events == [
        "connect:smtp.example.com:587:12.0",
        "enter",
        "tls",
        "login:user@example.com:secret",
        "send:candidate@example.com:Interview update",
        "exit",
    ]
