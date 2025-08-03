from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_uow, get_user_spotify_client
from app.api.pagination import PaginatedResponse, PaginationParams
from app.clients.spotify import UserSpotifyClient
from app.db.models.user import User
from app.db.uow import AbstractUnitOfWork
from app.schemas.raw_layer import (
    RawLayerBlockCreate,
    RawLayerBlockResponse,
    RawLayerBlockSummary,
)
from app.services.raw_layer import RawLayerService

router = APIRouter(prefix="/curation", tags=["curation"])


@router.post(
    "/styles/{style_id}/raw-blocks",
    response_model=RawLayerBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_raw_layer_block(
    style_id: int,
    block_in: RawLayerBlockCreate,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
):
    """
    Creates a new Raw Layer (Bronze) curation block for the current user.

    This is a transactional operation that:
    1. Selects tracks based on Beatport publish date and Spotify availability.
    2. Creates a structured set of playlists on Spotify (INBOX, TRASH, TARGETS).
    3. Persists the block and playlist metadata in the database.
    4. Categorizes and adds the selected tracks to the INBOX playlists.
    """
    raw_layer_service = RawLayerService(
        db=uow.session, user_spotify_client=user_spotify_client
    )
    return await raw_layer_service.create_raw_layer_block(
        style_id=style_id, block_in=block_in, user=current_user
    )


@router.get(
    "/styles/{style_id}/raw-blocks",
    response_model=PaginatedResponse[RawLayerBlockSummary],
)
async def get_raw_layer_blocks(
    style_id: int,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
) -> PaginatedResponse[RawLayerBlockSummary]:
    """
    Get a paginated list of raw layer blocks for a specific style and user.
    """
    raw_layer_service = RawLayerService(
        db=uow.session, user_spotify_client=user_spotify_client
    )
    return await raw_layer_service.get_user_blocks_by_style_paginated(
        user_id=current_user.id, style_id=style_id, params=pagination
    )


@router.get("/raw-blocks/{block_id}", response_model=RawLayerBlockResponse)
async def get_raw_layer_block(
    block_id: int,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
) -> RawLayerBlockResponse:
    """
    Get detailed information for a single raw layer block.
    """
    raw_layer_service = RawLayerService(
        db=uow.session, user_spotify_client=user_spotify_client
    )
    block = await raw_layer_service.get_block_by_id(
        block_id=block_id, user_id=current_user.id
    )
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Block not found"
        )
    return block


@router.post("/raw-blocks/{block_id}/process", response_model=RawLayerBlockResponse)
async def process_raw_layer_block(
    block_id: int,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
):
    """
    Marks a raw layer block as processed.
    """
    raw_layer_service = RawLayerService(
        db=uow.session, user_spotify_client=user_spotify_client
    )
    block = await raw_layer_service.process_block(
        block_id=block_id, user_id=current_user.id
    )
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Block not found"
        )
    return block
