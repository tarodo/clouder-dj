from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.clients.spotify import UserSpotifyClient
from app.core.constants import VALID_SPOTIFY_ALBUM_TYPES
from app.core.exceptions import RawLayerBlockExistsError, StyleNotFoundError
from app.db.models import Category, RawLayerBlock, Style, Track, User
from app.db.models.external_data import ExternalDataProvider
from app.db.models.raw_layer import (
    RawLayerBlockStatus,
    RawLayerPlaylist,
    RawLayerPlaylistType,
)
from app.repositories.category import CategoryRepository
from app.repositories.raw_layer import RawLayerRepository
from app.repositories.style import StyleRepository
from app.repositories.track import TrackRepository
from app.schemas.raw_layer import (
    RawLayerBlockCreate,
    RawLayerBlockResponse,
    RawLayerPlaylistResponse,
    RawLayerBlockSummary,
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
        self.track_repo = TrackRepository(db)

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
        self, *, style_id: int, block_in: RawLayerBlockCreate, user: User
    ) -> RawLayerBlockResponse:
        # 1. Validate input
        style = await self.style_repo.get(id=style_id)
        if not style:
            raise StyleNotFoundError(style_id=style_id)

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
        await self.db.refresh(db_block, ["playlists"])

        # 5. Categorize & add tracks to Spotify playlists
        log.info(
            "Categorizing and adding tracks to playlists", name=block_in.block_name
        )

        # Add small delay to let Spotify prepare the playlists for modification
        await asyncio.sleep(0.5)
        log.debug("Waited for Spotify playlists to be ready for modification")

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

        return RawLayerBlockResponse(
            id=db_block.id,
            name=db_block.name,
            status=db_block.status,
            start_date=db_block.start_date,
            end_date=db_block.end_date,
            playlists=[
                RawLayerPlaylistResponse.model_validate(p) for p in db_block.playlists
            ],
            track_count=len(selected_tracks),
        )

    async def get_user_blocks_paginated(
        self, *, user_id: int, params: PaginationParams
    ) -> PaginatedResponse[RawLayerBlockSummary]:
        blocks, total = await self.raw_layer_repo.get_paginated_by_user(
            user_id=user_id, params=params
        )

        summary_items = []
        for block in blocks:
            playlists_data = []
            for p in block.playlists:
                p_data = RawLayerPlaylistResponse.model_validate(p)
                if p.category:
                    p_data.category_name = p.category.name
                playlists_data.append(p_data)

            summary_items.append(
                RawLayerBlockSummary(
                    id=block.id,
                    name=block.name,
                    status=block.status,
                    start_date=block.start_date,
                    end_date=block.end_date,
                    track_count=len(block.tracks),
                    playlist_count=len(block.playlists),
                    playlists=playlists_data,
                )
            )

        return PaginatedResponse.create(
            items=summary_items,
            total=total,
            params=params,
        )

    async def get_user_blocks_by_style_paginated(
        self, *, user_id: int, style_id: int, params: PaginationParams
    ) -> PaginatedResponse[RawLayerBlockSummary]:
        blocks, total = await self.raw_layer_repo.get_paginated_by_user_and_style(
            user_id=user_id, style_id=style_id, params=params
        )

        summary_items = []
        for block in blocks:
            playlists_data = []
            for p in block.playlists:
                p_data = RawLayerPlaylistResponse.model_validate(p)
                if p.category:
                    p_data.category_name = p.category.name
                playlists_data.append(p_data)

            summary_items.append(
                RawLayerBlockSummary(
                    id=block.id,
                    name=block.name,
                    status=block.status,
                    start_date=block.start_date,
                    end_date=block.end_date,
                    track_count=len(block.tracks),
                    playlist_count=len(block.playlists),
                    playlists=playlists_data,
                )
            )

        return PaginatedResponse.create(
            items=summary_items,
            total=total,
            params=params,
        )

    async def get_block_by_id(
        self, *, block_id: int, user_id: int
    ) -> RawLayerBlockResponse | None:
        block = await self.raw_layer_repo.get_by_id_for_user(
            block_id=block_id, user_id=user_id
        )
        if not block:
            return None

        return RawLayerBlockResponse(
            id=block.id,
            name=block.name,
            status=block.status,
            start_date=block.start_date,
            end_date=block.end_date,
            playlists=[
                RawLayerPlaylistResponse.model_validate(p) for p in block.playlists
            ],
            track_count=len(block.tracks),
        )

    async def process_block(
        self, *, block_id: int, user_id: int
    ) -> RawLayerBlockResponse | None:
        block = await self.raw_layer_repo.get_by_id_for_user(
            block_id=block_id, user_id=user_id
        )
        if not block:
            return None

        log.info(
            "Processing block, persisting target playlist tracks", block_id=block.id
        )
        # lazy loading playlists
        await self.db.refresh(block, ["playlists"])
        target_playlists = [
            p for p in block.playlists if p.playlist_type == RawLayerPlaylistType.TARGET
        ]

        for playlist in target_playlists:
            log.info(
                "Fetching tracks for target playlist",
                playlist_id=playlist.spotify_playlist_id,
                playlist_db_id=playlist.id,
            )
            track_uris = await self.spotify_client.get_playlist_items(
                playlist_id=playlist.spotify_playlist_id
            )

            if not track_uris:
                log.info(
                    "No tracks found in target playlist, skipping",
                    playlist_id=playlist.spotify_playlist_id,
                )
                continue

            log.info(
                "Found tracks in target playlist, finding in local DB",
                playlist_id=playlist.spotify_playlist_id,
                track_count=len(track_uris),
            )
            found_tracks = await self.track_repo.find_by_spotify_uris(uris=track_uris)

            if found_tracks:
                log.info(
                    "Associating tracks with playlist in DB",
                    playlist_db_id=playlist.id,
                    found_track_count=len(found_tracks),
                )
                # lazy loading tracks
                await self.db.refresh(playlist, ["tracks"])
                playlist.tracks.extend(found_tracks)
            else:
                log.info(
                    "None of the tracks from Spotify playlist found in local DB",
                    playlist_id=playlist.spotify_playlist_id,
                )

        block.status = RawLayerBlockStatus.PROCESSED
        self.db.add(block)
        await self.db.flush()
        await self.db.refresh(block, ["playlists", "tracks"])

        return RawLayerBlockResponse(
            id=block.id,
            name=block.name,
            status=block.status,
            start_date=block.start_date,
            end_date=block.end_date,
            playlists=[
                RawLayerPlaylistResponse.model_validate(p) for p in block.playlists
            ],
            track_count=len(block.tracks),
        )
