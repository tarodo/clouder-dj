from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.track import Track
from app.repositories.base import BaseRepository


class TrackRepository(BaseRepository[Track]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Track, db=db)
