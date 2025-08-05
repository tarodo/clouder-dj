from __future__ import annotations

import asyncio
import re
from typing import Sequence

import structlog
from fastapi import HTTPException, status

from app.clients.spotify import UserSpotifyClient
from app.db.models import ReleasePlaylist, User
from app.db.models.external_data import ExternalDataProvider
from app.db.uow import AbstractUnitOfWork
from app.schemas.release_playlist import (
    ReleasePlaylistCreate,
    ReleasePlaylistImport,
    ReleasePlaylistSimple,
)

log = structlog.get_logger()

SPOTIFY_PLAYLIST_ID_REGEX = re.compile(r"(?<=playlist\/)([a-zA-Z0-9]+)")


class ReleasePlaylistService:
    def __init__(self, uow: AbstractUnitOfWork, spotify_client: UserSpotifyClient):
        self.uow = uow
        self.spotify_client = spotify_client

    def _parse_spotify_playlist_id(self, id_or_url: str) -> str | None:
        match = SPOTIFY_PLAYLIST_ID_REGEX.search(id_or_url)
        if match:
            return match.group(1)
        # Assume it's an ID if no match
        if "/" not in id_or_url and " " not in id_or_url:
            return id_or_url
        return None

    async def create_empty_playlist(
        self, *, playlist_in: ReleasePlaylistCreate, user: User
    ) -> ReleasePlaylist:
        playlist = ReleasePlaylist(**playlist_in.model_dump(), user_id=user.id)
        self.uow.session.add(playlist)
        await self.uow.session.flush()
        await self.uow.session.refresh(playlist)
        return playlist

    async def import_from_spotify(
        self, *, import_in: ReleasePlaylistImport, user: User
    ) -> ReleasePlaylist:
        playlist_id = self._parse_spotify_playlist_id(
            import_in.spotify_playlist_id_or_url
        )
        if not playlist_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Spotify Playlist ID or URL format.",
            )

        existing = await self.uow.release_playlists.get_by_spotify_playlist_id(
            spotify_playlist_id=playlist_id, user_id=user.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Playlist with Spotify ID {playlist_id} already exists",
            )

        playlist_details = await self.spotify_client.get_playlist(
            playlist_id=playlist_id
        )
        playlist_items = await self.spotify_client.get_playlist_all_items(
            playlist_id=playlist_id
        )

        spotify_uris = [item["uri"] for item in playlist_items if item.get("uri")]
        uri_to_position = {uri: i for i, uri in enumerate(spotify_uris)}

        local_tracks = await self.uow.tracks.find_by_spotify_uris(uris=spotify_uris)
        await asyncio.gather(
            *[self.uow.session.refresh(t, ["external_data"]) for t in local_tracks]
        )

        tracks_with_pos = []
        for track in local_tracks:
            spotify_uri = next(
                (
                    f"spotify:track:{ed.external_id}"
                    for ed in track.external_data
                    if ed.provider == ExternalDataProvider.SPOTIFY
                ),
                None,
            )
            if spotify_uri and spotify_uri in uri_to_position:
                position = uri_to_position[spotify_uri]
                tracks_with_pos.append((track, position))

        playlist = ReleasePlaylist(
            name=playlist_details["name"],
            description=playlist_details.get("description"),
            user_id=user.id,
            spotify_playlist_id=playlist_id,
            spotify_playlist_url=playlist_details.get("external_urls", {}).get(
                "spotify"
            ),
        )

        created_playlist = await self.uow.release_playlists.create_with_tracks(
            playlist=playlist, tracks_with_pos=tracks_with_pos
        )
        return created_playlist

    async def get_playlist_by_id(
        self, *, playlist_id: int, user: User
    ) -> ReleasePlaylist | None:
        return await self.uow.release_playlists.get_by_id(
            id=playlist_id, user_id=user.id
        )

    async def get_playlists_for_user(
        self, *, user: User
    ) -> Sequence[ReleasePlaylistSimple]:
        playlists_orm = await self.uow.release_playlists.get_all_for_user(
            user_id=user.id
        )
        return [ReleasePlaylistSimple.model_validate(p) for p in playlists_orm]
