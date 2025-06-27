from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

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
