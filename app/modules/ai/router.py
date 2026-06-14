from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ai.batch_match import (
    BatchMatchRequest,
    BatchMatchResult,
    BatchMatchService,
    get_batch_match_service,
)
from app.modules.ai.cover_letter_generation import (
    CoverLetterGenerationRequest,
    CoverLetterGenerationResult,
    OpenAICoverLetterGenerationService,
    get_cover_letter_generation_service,
)
from app.modules.ai.matching import (
    MatchAnalysis,
    MatchAnalysisRequest,
    OpenAIMatchingService,
    get_matching_service,
)
from app.modules.ai.resume_optimization import (
    OpenAIResumeOptimizationService,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    get_resume_optimization_service,
)
from app.modules.ai.schemas import GenerationRequest, TaskQueued
from app.modules.ai.semantic_shortlist import (
    OpenAIResumeShortlistService,
    ResumeShortlistAnalysis,
    ResumeShortlistRequest,
    get_resume_shortlist_service,
)
from app.modules.ai.tasks import generate_content
from app.modules.common import task_response

router = APIRouter()


@router.post("/generations", response_model=TaskQueued, status_code=status.HTTP_202_ACCEPTED)
async def start_generation(payload: GenerationRequest) -> dict[str, str]:
    task = generate_content.delay(payload.operation, payload.context)
    return task_response(task)


@router.post("/match", response_model=MatchAnalysis)
async def match_resume_to_job(
    payload: MatchAnalysisRequest,
    service: Annotated[OpenAIMatchingService, Depends(get_matching_service)],
) -> MatchAnalysis:
    return await service.analyze(payload)


@router.post("/match/batch", response_model=BatchMatchResult)
async def batch_match_jobs(
    payload: BatchMatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[BatchMatchService, Depends(get_batch_match_service)],
) -> BatchMatchResult:
    return await service.score(db, payload)


@router.post("/resume-optimization", response_model=ResumeOptimizationResult)
async def optimize_resume(
    payload: ResumeOptimizationRequest,
    service: Annotated[
        OpenAIResumeOptimizationService,
        Depends(get_resume_optimization_service),
    ],
) -> ResumeOptimizationResult:
    return await service.optimize(payload)


@router.post("/cover-letter", response_model=CoverLetterGenerationResult)
async def generate_cover_letter(
    payload: CoverLetterGenerationRequest,
    service: Annotated[
        OpenAICoverLetterGenerationService,
        Depends(get_cover_letter_generation_service),
    ],
) -> CoverLetterGenerationResult:
    return await service.generate(payload)


@router.post("/resume-shortlist", response_model=ResumeShortlistAnalysis)
async def shortlist_resumes_for_job(
    payload: ResumeShortlistRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[OpenAIResumeShortlistService, Depends(get_resume_shortlist_service)],
) -> ResumeShortlistAnalysis:
    return await service.shortlist(db, payload)
