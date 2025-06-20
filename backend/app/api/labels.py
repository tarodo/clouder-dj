from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.pagination import PaginatedResponse, PaginationParams
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
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[Label]:
    """
    Get a paginated list of labels.
    """
    label_service = LabelService(db)
    return await label_service.get_labels_paginated(params=pagination)
