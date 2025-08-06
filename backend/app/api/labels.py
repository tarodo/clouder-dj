from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_uow
from app.api.pagination import PaginatedResponse, PaginationParams
from app.db.uow import AbstractUnitOfWork
from app.schemas.label import Label
from app.services.label import LabelService

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get(
    "",
    response_model=PaginatedResponse[Label],
    dependencies=[Depends(get_current_user)],
)
async def get_labels(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        default=None, description="Case-insensitive search for label name"
    ),
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Label]:
    """
    Get a paginated list of labels.
    """
    label_service = LabelService(uow.session)
    return await label_service.get_labels_paginated(
        params=pagination, search_query=search
    )
