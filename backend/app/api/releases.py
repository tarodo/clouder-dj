from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_uow
from app.api.pagination import PaginatedResponse, PaginationParams
from app.db.uow import AbstractUnitOfWork
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
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Release]:
    """
    Get a paginated list of releases.
    """
    release_service = ReleaseService(uow.session)
    return await release_service.get_releases_paginated(params=pagination)
