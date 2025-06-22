from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.style import Style
from app.repositories.base import BaseRepository


class StyleRepository(BaseRepository[Style]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Style, db=db)
