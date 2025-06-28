from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.external_data import (
    ExternalData,
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.models.track import Track, track_artists
from app.repositories.base import BaseRepository


class TrackRepository(BaseRepository[Track]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Track, db=db)

    async def bulk_get_or_create_with_relations(
        self, tracks_data: List[dict[str, Any]]
    ) -> Dict[Tuple[str, int, str | None], Track]:
        """
        Efficiently gets or creates tracks and their M2M relationships with artists.
        `tracks_data` is a list of dicts, each with track attributes
        and an 'artist_ids' key, e.g.,
        [{'name': 'T1', 'release_id': 1, 'artist_ids': [1, 2]}, ...]
        Returns a dictionary mapping (name, release_id) to the corresponding Track.
        """
        if not tracks_data:
            return {}

        # Separate track core data from artist relations for insertion
        track_core_data = [
            {k: v for k, v in t.items() if k not in ["artist_ids", "external_id"]}
            for t in tracks_data
        ]

        # 1. Insert/Ignore: Use ON CONFLICT DO NOTHING to insert new tracks
        insert_stmt = insert(Track).values(track_core_data)
        on_conflict_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=["name", "release_id", "isrc"]
        )
        await self.db.execute(on_conflict_stmt)

        # 2. Select: Fetch all required tracks (both new and pre-existing)
        keys_to_fetch = {
            (t["name"], t["release_id"], t["isrc"]) for t in track_core_data
        }
        select_stmt = select(Track).where(
            tuple_(Track.name, Track.release_id, Track.isrc).in_(keys_to_fetch)  # type: ignore
        )
        result = await self.db.execute(select_stmt)
        fetched_tracks = result.scalars().all()
        tracks_map: Dict[Tuple[str, int, str | None], Track] = {
            (t.name, t.release_id, t.isrc): t for t in fetched_tracks
        }

        # 3. Prepare and bulk insert M2M artist associations
        artist_associations = []
        # Create a map of (name, release_id, isrc) -> artist_ids from original input
        artist_ids_map = {
            (t["name"], t["release_id"], t["isrc"]): t.get("artist_ids", [])
            for t in tracks_data
        }

        for key, track in tracks_map.items():
            for artist_id in artist_ids_map.get(key, []):
                artist_associations.append(
                    {"track_id": track.id, "artist_id": artist_id}
                )

        if artist_associations:
            # Deduplicate associations before inserting
            unique_associations = [
                dict(t) for t in {tuple(d.items()) for d in artist_associations}
            ]
            await self.db.execute(
                insert(track_artists)
                .values(unique_associations)
                .on_conflict_do_nothing()
            )

        return tracks_map

    async def get_tracks_missing_spotify_link(
        self, *, offset: int, limit: int
    ) -> Tuple[List[Track], int]:
        """
        Gets tracks that have an ISRC but no associated Spotify external data link.

        This method uses a NOT EXISTS subquery to efficiently find tracks that are
        missing a corresponding entry in the external_data table for the SPOTIFY
        provider. It also preloads the 'artists' relationship for the returned tracks.

        Args:
            offset: The number of records to skip for pagination.
            limit: The maximum number of records to return.

        Returns:
            A tuple containing a list of Track objects and the total count of
            all such tracks in the database.
        """
        # Define the NOT EXISTS subquery condition
        exists_condition = (
            select(ExternalData.id)
            .where(
                ExternalData.provider == ExternalDataProvider.SPOTIFY,
                ExternalData.entity_type == ExternalDataEntityType.TRACK,
                ExternalData.entity_id == Track.id,
            )
            .exists()
        )

        # Base query to find tracks with ISRC and where the Spotify link does not exist
        base_query = select(Track).where(
            Track.isrc.is_not(None),
            ~exists_condition,
        )

        # Query for total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        if total == 0:
            return [], 0

        # Query for the paginated items with artists preloaded
        items_query = (
            base_query.options(joinedload(Track.artists))
            .order_by(Track.id)
            .offset(offset)
            .limit(limit)
        )
        items_result = await self.db.execute(items_query)
        items = list(items_result.scalars().unique().all())

        return items, total

    async def get_tracks_by_artist_ids_with_spotify_data(
        self, *, artist_ids: List[int]
    ) -> List[Track]:
        """
        Gets tracks for a given list of artist IDs that have a Spotify data link.
        Preloads artists and attaches the relevant external_data record.
        """
        if not artist_ids:
            return []

        # This query fetches Tracks and their associated Spotify ExternalData.
        # It filters by artist_ids and ensures a Spotify link exists.
        stmt = (
            select(Track, ExternalData)
            .join(track_artists, Track.id == track_artists.c.track_id)
            .join(
                ExternalData,
                (ExternalData.entity_id == Track.id)
                & (ExternalData.entity_type == ExternalDataEntityType.TRACK)
                & (ExternalData.provider == ExternalDataProvider.SPOTIFY)
                & (ExternalData.raw_data.is_not(None)),
            )
            .where(track_artists.c.artist_id.in_(artist_ids))
            .options(joinedload(Track.artists))
            .distinct()
        )

        result = await self.db.execute(stmt)

        track_map: Dict[int, Track] = {}
        for track, ext_data in result.unique().all():
            if track.id not in track_map:
                # NOTE: Monkey-patching external_data onto the Track object.
                # The service layer will need to be aware of this.
                track.external_data = []  # type: ignore
                track_map[track.id] = track
            track_map[track.id].external_data.append(ext_data)  # type: ignore

        return list(track_map.values())
