from sqlalchemy import select

from backend.models.label import Label
from backend.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    model = Label

    async def get_by_name(self, name: str) -> Label | None:
        """Get a label by name."""
        query = select(self.model).where(self.model.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_code(self, code: str) -> Label | None:
        """Get a label by code."""
        query = select(self.model).where(self.model.code == code)
        result = await self.session.execute(query)
        return result.scalars().first()

