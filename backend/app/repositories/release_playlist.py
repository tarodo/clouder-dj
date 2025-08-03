from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ReleasePlaylist, ReleasePlaylistTrack, Track
from app.repositories.base import BaseRepository


class ReleasePlaylistRepository(BaseRepository[ReleasePlaylist]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=ReleasePlaylist, db=db)

    async def create_with_tracks(
        self, *, playlist: ReleasePlaylist, tracks_with_pos: list[tuple[Track, int]]
    ) -> ReleasePlaylist:
        self.db.add(playlist)
        await self.db.flush()  # Get playlist ID

        playlist_tracks = [
            ReleasePlaylistTrack(
                release_playlist_id=playlist.id,
                track_id=track.id,
                position=pos,
            )
            for track, pos in tracks_with_pos
        ]
        self.db.add_all(playlist_tracks)
        await self.db.flush()
        # The refresh call can cause a KeyError. Re-fetching the object with
        # selectinload is a more reliable way to get the fully populated object.
        stmt = (
            select(ReleasePlaylist)
            .where(ReleasePlaylist.id == playlist.id)
            .options(
                selectinload(ReleasePlaylist.tracks).selectinload(
                    ReleasePlaylistTrack.track
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().one()

    async def get_by_id(self, *, id: int, user_id: int) -> ReleasePlaylist | None:
        stmt = (
            select(ReleasePlaylist)
            .options(
                selectinload(ReleasePlaylist.tracks).selectinload(
                    ReleasePlaylistTrack.track
                )
            )
            .where(ReleasePlaylist.id == id, ReleasePlaylist.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_for_user(self, *, user_id: int) -> Sequence[ReleasePlaylist]:
        stmt = select(ReleasePlaylist).where(ReleasePlaylist.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_spotify_playlist_id(
        self, *, spotify_playlist_id: str, user_id: int
    ) -> ReleasePlaylist | None:
        stmt = select(ReleasePlaylist).where(
            ReleasePlaylist.spotify_playlist_id == spotify_playlist_id,
            ReleasePlaylist.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
