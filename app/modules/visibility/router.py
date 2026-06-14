from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.visibility.schemas import VisibilityRequest, VisibilityResult
from app.modules.visibility.service import VisibilityService, get_visibility_service

router = APIRouter()


@router.post("", response_model=VisibilityResult)
async def analyze_visibility(
    payload: VisibilityRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[VisibilityService, Depends(get_visibility_service)],
) -> VisibilityResult:
    return await service.analyze(db, payload)
