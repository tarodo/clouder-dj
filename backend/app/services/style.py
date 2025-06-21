from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.repositories.style import StyleRepository
from app.schemas.style import Style as StyleSchema


class StyleService:
    def __init__(self, db: AsyncSession):
        self.style_repo = StyleRepository(db)

    async def get_styles_paginated(
        self, *, params: PaginationParams
    ) -> PaginatedResponse[StyleSchema]:
        styles, total = await self.style_repo.get_paginated(params=params)
        return PaginatedResponse.create(
            items=[StyleSchema.model_validate(style) for style in styles],
            total=total,
            params=params,
        )
