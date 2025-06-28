from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.artist import Artist
from app.db.models.external_data import (
    ExternalData,
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.repositories.base import BaseRepository


class ArtistRepository(BaseRepository[Artist]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Artist, db=db)

    async def bulk_get_or_create_by_name(self, names: List[str]) -> Dict[str, Artist]:
        """
        Efficiently gets or creates artists by name.
        Returns a dictionary mapping name to Artist object.
        """
        if not names:
            return {}

        unique_names = sorted(list(set(names)))

        # Attempt to insert all, ignoring conflicts for existing names
        insert_stmt = insert(Artist).values([{"name": name} for name in unique_names])
        on_conflict_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["name"])
        await self.db.execute(on_conflict_stmt)

        # Fetch all required artists (both existing and newly created)
        select_stmt = select(Artist).where(Artist.name.in_(unique_names))
        result = await self.db.execute(select_stmt)
        artists = result.scalars().all()

        return {artist.name: artist for artist in artists}

    async def get_artists_missing_spotify_link(
        self, *, offset: int, limit: int
    ) -> Tuple[List[Artist], int]:
        """
        Gets artists that do not have an associated Spotify external data link.
        """
        exists_condition = (
            select(ExternalData.id)
            .where(
                ExternalData.provider == ExternalDataProvider.SPOTIFY,
                ExternalData.entity_type == ExternalDataEntityType.ARTIST,
                ExternalData.entity_id == Artist.id,
            )
            .exists()
        )

        base_query = select(Artist).where(~exists_condition)

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        if total == 0:
            return [], 0

        items_query = base_query.order_by(Artist.id).offset(offset).limit(limit)
        items_result = await self.db.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total
