from __future__ import annotations

from typing import Generic, List, Tuple, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginationParams
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_paginated(
        self, *, params: PaginationParams
    ) -> Tuple[List[ModelType], int]:
        offset = (params.page - 1) * params.per_page

        items_query = (
            select(self.model)
            .order_by(self.model.id)
            .offset(offset)
            .limit(params.per_page)
        )
        items_result = await self.db.execute(items_query)
        items = list(items_result.scalars().all())

        total_query = select(func.count()).select_from(self.model)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        return items, total
