from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.repositories.label import LabelRepository
from app.schemas.label import Label as LabelSchema


class LabelService:
    def __init__(self, db: AsyncSession):
        self.label_repo = LabelRepository(db)

    async def get_labels_paginated(
        self, *, params: PaginationParams, search_query: str | None = None
    ) -> PaginatedResponse[LabelSchema]:
        labels, total = await self.label_repo.get_paginated(
            params=params, search_query=search_query
        )
        return PaginatedResponse.create(
            items=[LabelSchema.model_validate(label) for label in labels],
            total=total,
            params=params,
        )
