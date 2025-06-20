from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.release import Release
from app.repositories.base import BaseRepository


class ReleaseRepository(BaseRepository[Release]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Release, db=db)
