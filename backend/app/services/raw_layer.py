from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import UserSpotifyClient
from app.core.constants import VALID_SPOTIFY_ALBUM_TYPES
from app.core.exceptions import RawLayerBlockExistsError, StyleNotFoundError
from app.db.models import Category, RawLayerBlock, Style, Track, User
from app.db.models.external_data import ExternalDataProvider
from app.db.models.raw_layer import RawLayerPlaylist, RawLayerPlaylistType
from app.repositories.category import CategoryRepository
from app.repositories.raw_layer import RawLayerRepository
from app.repositories.style import StyleRepository
from app.schemas.raw_layer import (
    RawLayerBlockCreate,
    RawLayerBlockResponse,
    RawLayerPlaylistResponse,
)

log = structlog.get_logger()


class RawLayerService:
    def __init__(
        self,
        db: AsyncSession,
        user_spotify_client: UserSpotifyClient,
    ):
        self.db = db
        self.spotify_client = user_spotify_client
        self.raw_layer_repo = RawLayerRepository(db)
        self.style_repo = StyleRepository(db)
        self.category_repo = CategoryRepository(db)

    async def _create_spotify_playlists(
        self,
        block_name: str,
        style: Style,
        target_categories: List[Category],
    ) -> List[Dict[str, Any]]:
        playlist_definitions = [
            {
                "name": f"INBOX // {block_name} // NEW",
                "type": RawLayerPlaylistType.INBOX_NEW,
            },
            {
                "name": f"INBOX // {block_name} // OLD",
                "type": RawLayerPlaylistType.INBOX_OLD,
            },
            {
                "name": f"INBOX // {block_name} // NOT",
                "type": RawLayerPlaylistType.INBOX_NOT,
            },
            {"name": f"TRASH // {block_name}", "type": RawLayerPlaylistType.TRASH},
        ]
        for category in target_categories:
            playlist_definitions.append(
                {
                    "name": f"TARGET // {block_name} // {category.name.upper()}",
                    "type": RawLayerPlaylistType.TARGET,
                    "category_id": category.id,  # type: ignore
                }
            )

        playlist_creation_tasks = []
        for p_def in playlist_definitions:
            playlist_type = p_def["type"]
            task = self.spotify_client.create_playlist(
                name=p_def["name"],
                public=False,
                description=f"Clouder-DJ Raw Layer Playlist ({playlist_type.value})",  # type: ignore
            )
            playlist_creation_tasks.append(task)

        created_spotify_playlists = await asyncio.gather(*playlist_creation_tasks)

        db_playlists_data = []
        for i, p_def in enumerate(playlist_definitions):
            spotify_playlist = created_spotify_playlists[i]
            db_playlists_data.append(
                {
                    "playlist_type": p_def["type"],
                    "category_id": p_def.get("category_id"),
                    "spotify_playlist_id": spotify_playlist["id"],
                    "spotify_playlist_url": spotify_playlist["external_urls"][
                        "spotify"
                    ],
                }
            )
        return db_playlists_data

    def _categorize_tracks(
        self, tracks: List[Track], start_date: date
    ) -> dict[RawLayerPlaylistType, list[str]]:
        categorized_uris: dict[RawLayerPlaylistType, list[str]] = {
            RawLayerPlaylistType.INBOX_NEW: [],
            RawLayerPlaylistType.INBOX_OLD: [],
            RawLayerPlaylistType.INBOX_NOT: [],
        }
        for track in tracks:
            spotify_data = next(
                (
                    d.raw_data
                    for d in track.external_data
                    if d.provider == ExternalDataProvider.SPOTIFY and d.raw_data
                ),
                None,
            )
            if not spotify_data:
                continue

            album = spotify_data.get("album", {})
            release_date_str = album.get("release_date")
            album_type = album.get("album_type")
            spotify_uri = spotify_data.get("uri")

            if not release_date_str or not album_type or not spotify_uri:
                continue

            try:
                # Spotify release_date can be YYYY, YYYY-MM, or YYYY-MM-DD
                release_date = datetime.fromisoformat(
                    release_date_str.split("T")[0]
                ).date()
            except ValueError:
                log.warning("Could not parse release date", date=release_date_str)
                continue

            if album_type not in VALID_SPOTIFY_ALBUM_TYPES:
                categorized_uris[RawLayerPlaylistType.INBOX_NOT].append(spotify_uri)
            elif release_date >= start_date:
                categorized_uris[RawLayerPlaylistType.INBOX_NEW].append(spotify_uri)
            else:
                categorized_uris[RawLayerPlaylistType.INBOX_OLD].append(spotify_uri)

        return categorized_uris

    async def create_raw_layer_block(
        self, *, block_in: RawLayerBlockCreate, user: User
    ) -> RawLayerBlockResponse:
        # 1. Validate input
        style = await self.style_repo.get(id=block_in.style_id)
        if not style:
            raise StyleNotFoundError(style_id=block_in.style_id)

        existing_block = await self.raw_layer_repo.get_by_user_style_and_name(
            user_id=user.id, style_id=style.id, name=block_in.block_name
        )
        if existing_block:
            raise RawLayerBlockExistsError(block_name=block_in.block_name)

        target_categories = await self.category_repo.get_by_user_and_style(
            user_id=user.id, style_id=style.id
        )

        # 2. Select tracks from DB
        log.info("Selecting tracks for raw layer block", name=block_in.block_name)
        selected_tracks = await self.raw_layer_repo.select_tracks_for_block(
            start_date=block_in.start_date,
            end_date=block_in.end_date,
        )
        log.info("Selected tracks", count=len(selected_tracks))

        # 3. Create playlists on Spotify API
        log.info("Creating Spotify playlists", name=block_in.block_name)
        db_playlists_data = await self._create_spotify_playlists(
            block_name=block_in.block_name,
            style=style,
            target_categories=target_categories,
        )

        # 4. Create DB records for block & playlists
        log.info("Creating DB records", name=block_in.block_name)
        db_block = RawLayerBlock(
            name=block_in.block_name,
            user_id=user.id,
            style_id=style.id,
            start_date=block_in.start_date,
            end_date=block_in.end_date,
            tracks=selected_tracks,
        )
        for p_data in db_playlists_data:
            db_block.playlists.append(RawLayerPlaylist(**p_data))

        self.db.add(db_block)
        await self.db.flush()

        # 5. Categorize & add tracks to Spotify playlists
        log.info(
            "Categorizing and adding tracks to playlists", name=block_in.block_name
        )
        categorized_uris = self._categorize_tracks(selected_tracks, block_in.start_date)

        playlist_map = {
            p.playlist_type: p.spotify_playlist_id for p in db_block.playlists
        }
        add_track_tasks = []
        for p_type, uris in categorized_uris.items():
            if uris and p_type in playlist_map:
                task = self.spotify_client.add_items_to_playlist(
                    playlist_id=playlist_map[p_type], track_uris=uris
                )
                add_track_tasks.append(task)

        if add_track_tasks:
            await asyncio.gather(*add_track_tasks)

        # Load all data before commit to avoid lazy loading after session closes
        block_id = db_block.id
        block_name = db_block.name
        block_start_date = db_block.start_date
        block_end_date = db_block.end_date
        # Load all playlist attributes to avoid lazy loading
        block_playlists = []
        for playlist in db_block.playlists:
            block_playlists.append(
                RawLayerPlaylistResponse(
                    playlist_type=playlist.playlist_type,
                    spotify_playlist_id=playlist.spotify_playlist_id,
                    spotify_playlist_url=playlist.spotify_playlist_url,
                    category_id=playlist.category_id,
                )
            )

        return RawLayerBlockResponse(
            id=block_id,
            name=block_name,
            start_date=block_start_date,
            end_date=block_end_date,
            playlists=block_playlists,
            track_count=len(selected_tracks),
        )
