from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.repositories.track import TrackRepository
from app.schemas.track import Track as TrackSchema


class TrackService:
    def __init__(self, db: AsyncSession):
        self.track_repo = TrackRepository(db)

    async def get_tracks_paginated(
        self, *, params: PaginationParams, search_query: str | None = None
    ) -> PaginatedResponse[TrackSchema]:
        tracks, total = await self.track_repo.get_paginated(
            params=params, search_query=search_query
        )
        return PaginatedResponse.create(
            items=[TrackSchema.model_validate(track) for track in tracks],
            total=total,
            params=params,
        )
