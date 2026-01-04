from sqlalchemy import select

from backend.models.track import Track
from backend.repositories.base import BaseRepository


class TrackRepository(BaseRepository[Track]):
    model = Track

    async def get_by_isrc(self, isrc: str) -> Track | None:
        """Get a track by ISRC."""
        query = select(self.model).where(self.model.isrc == isrc)
        result = await self.session.execute(query)
        return result.scalars().first()

