"""Import all models so SQLAlchemy and Alembic can discover their metadata."""

from app.modules.applications.model import Application
from app.modules.cover_letters.model import CoverLetter
from app.modules.job_matches.model import JobMatch
from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume
from app.modules.users.model import User

__all__ = ["Application", "CoverLetter", "Job", "JobMatch", "Resume", "User"]
