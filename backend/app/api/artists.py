from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_uow
from app.api.pagination import PaginatedResponse, PaginationParams
from app.db.uow import AbstractUnitOfWork
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
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Artist]:
    """
    Get a paginated list of artists.
    """
    artist_service = ArtistService(uow.session)
    return await artist_service.get_artists_paginated(
        params=pagination, search_query=search
    )
