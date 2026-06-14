from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.applications.router import router as applications_router
from app.modules.cover_letters.router import router as cover_letters_router
from app.modules.jobs.router import router as jobs_router
from app.modules.resumes.router import router as resumes_router
from app.modules.scrapers.router import router as scrapers_router
from app.modules.stats.router import router as stats_router
from app.modules.visibility.router import router as visibility_router

api_router = APIRouter()
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(cover_letters_router, prefix="/cover-letters", tags=["cover-letters"])
api_router.include_router(scrapers_router, prefix="/scrapers", tags=["scrapers"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(visibility_router, prefix="/ai/visibility", tags=["ai"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
