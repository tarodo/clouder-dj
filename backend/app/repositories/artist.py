from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.models.artist import Artist
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
