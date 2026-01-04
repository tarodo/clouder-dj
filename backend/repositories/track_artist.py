import uuid

from sqlalchemy import select

from backend.models.track_artist import TrackArtist
from backend.repositories.base import BaseRepository


class TrackArtistRepository(BaseRepository[TrackArtist]):
    model = TrackArtist

    async def get_by_pair(
        self, artist_id: uuid.UUID, track_id: uuid.UUID
    ) -> TrackArtist | None:
        query = select(self.model).where(
            self.model.artist_id == artist_id, self.model.track_id == track_id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

