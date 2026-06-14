import logging
from typing import Any

from app.core.celery_app import celery_app
from app.modules.ai.cover_letter_generation import (
    CoverLetterGenerationRequest,
    CoverLetterTone,
    get_cover_letter_generation_service,
)
from app.modules.ai.matching import MatchAnalysisRequest, get_matching_service
from app.modules.ai.resume_optimization import (
    ResumeOptimizationRequest,
    get_resume_optimization_service,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_content(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
    """LLM provider adapters should replace this body while preserving its queue contract."""
    logger.info(
        "ai_generation_requested",
        extra={"operation": operation, "task_id": self.request.id},
    )
    return {"operation": operation, "context": context, "status": "accepted"}


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_match(self, resume_text: str, job_description: str) -> dict[str, Any]:
    import asyncio

    service = get_matching_service()
    result = asyncio.run(
        service.analyze(
            MatchAnalysisRequest(
                resume_text=resume_text,
                job_description=job_description,
            )
        )
    )
    logger.info(
        "ai_match_analyzed",
        extra={"task_id": self.request.id, "match_score": result.match_score},
    )
    return result.model_dump()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def optimize_resume(self, resume_markdown: str, job_description: str) -> dict[str, Any]:
    import asyncio

    service = get_resume_optimization_service()
    result = asyncio.run(
        service.optimize(
            ResumeOptimizationRequest(
                resume_markdown=resume_markdown,
                job_description=job_description,
            )
        )
    )
    logger.info(
        "ai_resume_optimized",
        extra={"task_id": self.request.id, "result_length": len(result.optimized_markdown)},
    )
    return result.model_dump()


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_cover_letter(
    self,
    resume_text: str,
    job_description: str,
    tone: CoverLetterTone = "formal",
) -> dict[str, Any]:
    import asyncio

    service = get_cover_letter_generation_service()
    result = asyncio.run(
        service.generate(
            CoverLetterGenerationRequest(
                resume_text=resume_text,
                job_description=job_description,
                tone=tone,
            )
        )
    )
    logger.info(
        "ai_cover_letter_generated",
        extra={
            "task_id": self.request.id,
            "tone": tone,
            "result_length": len(result.cover_letter_markdown),
        },
    )
    return result.model_dump()
