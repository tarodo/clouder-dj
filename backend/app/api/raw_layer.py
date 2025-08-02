from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_uow, get_user_spotify_client
from app.clients.spotify import UserSpotifyClient
from app.db.models.user import User
from app.db.uow import AbstractUnitOfWork
from app.schemas.raw_layer import RawLayerBlockCreate, RawLayerBlockResponse
from app.services.raw_layer import RawLayerService

router = APIRouter(prefix="/curation", tags=["curation"])


@router.post(
    "/raw-blocks",
    response_model=RawLayerBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_raw_layer_block(
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
        block_in=block_in, user=current_user
    )
