from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.repositories.base import BaseRepository
from app.schemas.category import CategoryCreateInternal, CategoryUpdate


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Category, db=db)

    async def get(self, *, id: int) -> Category | None:
        result = await self.db.execute(select(Category).filter(Category.id == id))
        return result.scalars().first()

    async def get_by_user_and_style(
        self, *, user_id: int, style_id: int
    ) -> List[Category]:
        stmt = select(Category).where(
            Category.user_id == user_id, Category.style_id == style_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_style_and_name(
        self, *, user_id: int, style_id: int, name: str
    ) -> Category | None:
        stmt = select(Category).where(
            Category.user_id == user_id,
            Category.style_id == style_id,
            Category.name == name,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, *, obj_in: CategoryCreateInternal) -> Category:
        db_obj = Category(**obj_in.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, *, db_obj: Category, obj_in: CategoryUpdate) -> Category:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: int) -> Category | None:
        db_obj = await self.get(id=id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
        return db_obj
