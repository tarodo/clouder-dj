from __future__ import annotations

from typing import Any, List

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.db.models.track import Track, track_artists


class TrackRepository(BaseRepository[Track]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Track, db=db)

    async def bulk_create_with_relations(
        self, tracks_data: List[dict[str, Any]]
    ) -> List[Track]:
        """
        Bulk creates tracks and their M2M relationships with artists.
        `tracks_data` is a list of dicts, each with track attributes
        and an 'artist_ids' key, e.g.,
        [{'name': 'T1', 'release_id': 1, 'artist_ids': [1, 2]}, ...]
        Returns a list of the newly created Track objects
        (without relationships loaded).
        """
        if not tracks_data:
            return []

        # Separate track core data from artist relations
        track_core_data = [
            {k: v for k, v in t.items() if k not in ["artist_ids", "external_id"]}
            for t in tracks_data
        ]

        # Bulk insert tracks and get their new IDs
        insert_stmt = insert(Track).values(track_core_data).returning(Track.id)
        result = await self.db.execute(insert_stmt)
        created_track_ids = result.scalars().all()

        # Prepare artist associations
        artist_associations = []
        for i, track_data in enumerate(tracks_data):
            track_id = created_track_ids[i]
            for artist_id in track_data.get("artist_ids", []):
                artist_associations.append(
                    {"track_id": track_id, "artist_id": artist_id}
                )

        # Bulk insert associations, ignoring any potential duplicates
        if artist_associations:
            unique_associations = [
                dict(t) for t in {tuple(d.items()) for d in artist_associations}
            ]
            await self.db.execute(
                insert(track_artists)
                .values(unique_associations)
                .on_conflict_do_nothing()
            )

        # Construct and return Track objects without an extra SELECT query
        created_tracks = []
        for i, core_data in enumerate(track_core_data):
            track = Track(**core_data, id=created_track_ids[i])
            created_tracks.append(track)

        return created_tracks
