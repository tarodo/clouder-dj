from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.pagination import PaginatedResponse, PaginationParams
from app.schemas.track import Track
from app.services.track import TrackService

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get(
    "",
    response_model=PaginatedResponse[Track],
    dependencies=[Depends(get_current_user)],
)
async def get_tracks(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        default=None, description="Case-insensitive search for track name"
    ),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[Track]:
    """
    Get a paginated list of tracks.
    """
    track_service = TrackService(db)
    return await track_service.get_tracks_paginated(
        params=pagination, search_query=search
    )
