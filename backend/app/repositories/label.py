from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.label import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Label, db=db)
