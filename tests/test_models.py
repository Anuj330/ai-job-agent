from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.db.models import Application, CoverLetter, Job, JobMatch, Resume, User


def test_all_requested_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "applications",
        "cover_letters",
        "job_matches",
        "jobs",
        "resumes",
        "users",
    }


def test_model_relationships_configure() -> None:
    configure_mappers()

    assert set(inspect(User).relationships.keys()) == {
        "applications",
        "cover_letters",
        "job_matches",
        "resumes",
    }
    assert set(inspect(Job).relationships.keys()) == {
        "applications",
        "cover_letters",
        "matches",
    }
    assert set(inspect(Resume).relationships.keys()) == {
        "applications",
        "cover_letters",
        "job_matches",
        "user",
    }
    assert set(inspect(CoverLetter).relationships.keys()) == {
        "applications",
        "job",
        "resume",
        "user",
    }
    assert set(inspect(JobMatch).relationships.keys()) == {"job", "resume", "user"}
    assert set(inspect(Application).relationships.keys()) == {
        "cover_letter",
        "job",
        "resume",
        "user",
    }


def test_workflow_uniqueness_constraints() -> None:
    application_constraints = {constraint.name for constraint in Application.__table__.constraints}
    match_constraints = {constraint.name for constraint in JobMatch.__table__.constraints}

    assert "uq_applications_user_job" in application_constraints
    assert "uq_job_matches_user_job_resume" in match_constraints
