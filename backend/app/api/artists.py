from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.pagination import PaginatedResponse, PaginationParams
from app.schemas.artist import Artist
from app.services.artist import ArtistService

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get(
    "",
    response_model=PaginatedResponse[Artist],
    dependencies=[Depends(get_current_user)],
)
async def get_artists(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        default=None, description="Case-insensitive search for artist name"
    ),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[Artist]:
    """
    Get a paginated list of artists.
    """
    artist_service = ArtistService(db)
    return await artist_service.get_artists_paginated(
        params=pagination, search_query=search
    )
