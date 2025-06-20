from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.repositories.release import ReleaseRepository
from app.schemas.release import Release as ReleaseSchema


class ReleaseService:
    def __init__(self, db: AsyncSession):
        self.release_repo = ReleaseRepository(db)

    async def get_releases_paginated(
        self, *, params: PaginationParams
    ) -> PaginatedResponse[ReleaseSchema]:
        releases, total = await self.release_repo.get_paginated(params=params)
        return PaginatedResponse.create(
            items=[ReleaseSchema.model_validate(release) for release in releases],
            total=total,
            params=params,
        )
