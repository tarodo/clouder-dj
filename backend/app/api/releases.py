from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.pagination import PaginatedResponse, PaginationParams
from app.schemas.release import Release
from app.services.release import ReleaseService

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get(
    "",
    response_model=PaginatedResponse[Release],
    dependencies=[Depends(get_current_user)],
)
async def get_releases(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[Release]:
    """
    Get a paginated list of releases.
    """
    release_service = ReleaseService(db)
    return await release_service.get_releases_paginated(params=pagination)
