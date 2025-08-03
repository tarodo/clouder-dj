from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_uow, get_user_spotify_client
from app.clients.spotify import UserSpotifyClient
from app.db.models import User
from app.db.uow import AbstractUnitOfWork
from app.schemas.release_playlist import (
    ReleasePlaylist,
    ReleasePlaylistCreate,
    ReleasePlaylistImport,
    ReleasePlaylistSimple,
)
from app.services.release_playlist import ReleasePlaylistService

router = APIRouter(prefix="/release-playlists", tags=["release-playlists"])


def get_release_playlist_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
) -> ReleasePlaylistService:
    return ReleasePlaylistService(uow=uow, spotify_client=spotify_client)


@router.post(
    "",
    response_model=ReleasePlaylist,
    status_code=status.HTTP_201_CREATED,
)
async def create_release_playlist(
    playlist_in: ReleasePlaylistCreate,
    current_user: User = Depends(get_current_user),
    service: ReleasePlaylistService = Depends(get_release_playlist_service),
):
    """Create a new, empty release playlist."""
    playlist = await service.create_empty_playlist(
        playlist_in=playlist_in, user=current_user
    )
    return playlist


@router.post(
    "/import",
    response_model=ReleasePlaylist,
    status_code=status.HTTP_201_CREATED,
)
async def import_spotify_playlist(
    import_in: ReleasePlaylistImport,
    current_user: User = Depends(get_current_user),
    service: ReleasePlaylistService = Depends(get_release_playlist_service),
):
    """Import a playlist from Spotify, linking only existing tracks."""
    playlist = await service.import_from_spotify(import_in=import_in, user=current_user)
    return playlist


@router.get("", response_model=List[ReleasePlaylistSimple])
async def get_user_release_playlists(
    current_user: User = Depends(get_current_user),
    service: ReleasePlaylistService = Depends(get_release_playlist_service),
):
    """Get all release playlists for the current user."""
    playlists = await service.get_playlists_for_user(user=current_user)
    return playlists


@router.get("/{playlist_id}", response_model=ReleasePlaylist)
async def get_release_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    service: ReleasePlaylistService = Depends(get_release_playlist_service),
):
    """Get a single release playlist by its ID."""
    playlist = await service.get_playlist_by_id(
        playlist_id=playlist_id, user=current_user
    )
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found"
        )
    return playlist
