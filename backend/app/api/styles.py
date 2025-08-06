from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_uow
from app.api.pagination import PaginatedResponse, PaginationParams
from app.db.uow import AbstractUnitOfWork
from app.schemas.style import Style
from app.services.style import StyleService

router = APIRouter(prefix="/styles", tags=["styles"])


@router.get(
    "",
    response_model=PaginatedResponse[Style],
    dependencies=[Depends(get_current_user)],
)
async def get_styles(
    pagination: PaginationParams = Depends(),
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Style]:
    """
    Get a paginated list of styles.
    """
    style_service = StyleService(uow.session)
    return await style_service.get_styles_paginated(params=pagination)
