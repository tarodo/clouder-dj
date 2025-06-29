from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.style import Style
from app.repositories.base import BaseRepository


class StyleRepository(BaseRepository[Style]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Style, db=db)

    async def get(self, *, id: int) -> Style | None:
        result = await self.db.execute(select(Style).filter(Style.id == id))
        return result.scalars().first()
