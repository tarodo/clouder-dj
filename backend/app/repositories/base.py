from __future__ import annotations

from typing import Any, Generic, List, Protocol, Tuple, Type, TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginationParams
from app.db.base_class import Base


class NamedModel(Protocol):
    """Protocol for models that have a name attribute."""

    name: Any  # SQLAlchemy column with ilike method


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_paginated(
        self, *, params: PaginationParams, search_query: str | None = None
    ) -> Tuple[List[ModelType], int]:
        offset = (params.page - 1) * params.per_page

        base_query = select(self.model)
        if search_query:
            # Cast to NamedModel to tell mypy that this model has a name attribute
            named_model = cast(Type[NamedModel], self.model)
            base_query = base_query.where(named_model.name.ilike(f"%{search_query}%"))

        items_query = (
            base_query.order_by(self.model.id).offset(offset).limit(params.per_page)
        )
        items_result = await self.db.execute(items_query)
        items = list(items_result.scalars().all())

        total_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        return items, total

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return result.scalar_one()
