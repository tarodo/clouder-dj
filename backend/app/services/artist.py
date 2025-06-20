from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import PaginatedResponse, PaginationParams
from app.repositories.artist import ArtistRepository
from app.schemas.artist import Artist as ArtistSchema


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.artist_repo = ArtistRepository(db)

    async def get_artists_paginated(
        self, *, params: PaginationParams
    ) -> PaginatedResponse[ArtistSchema]:
        artists, total = await self.artist_repo.get_paginated(params=params)
        return PaginatedResponse.create(
            items=[ArtistSchema.model_validate(artist) for artist in artists],
            total=total,
            params=params,
        )
