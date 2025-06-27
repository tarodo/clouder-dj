from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.models.release import Release
from app.repositories.base import BaseRepository


class ReleaseRepository(BaseRepository[Release]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Release, db=db)

    async def bulk_get_or_create(
        self, releases_data: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, int | None], Release]:
        """
        Efficiently gets or creates releases.
        `releases_data` is a list of dicts, e.g.,
        [{'name': '...', 'label_id': ...}]
        Returns a dictionary mapping (name, label_id) to Release object.
        """
        if not releases_data:
            return {}

        # Use ON CONFLICT with the unique constraint on (name, label_id)
        insert_stmt = insert(Release).values(releases_data)
        on_conflict_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=["name", "label_id"]
        )
        await self.db.execute(on_conflict_stmt)

        # Fetch all required releases using a tuple_ IN clause
        keys_to_fetch = {(r["name"], r["label_id"]) for r in releases_data}
        select_stmt = select(Release).where(
            tuple_(Release.name, Release.label_id).in_(keys_to_fetch)
        )
        result = await self.db.execute(select_stmt)
        releases = result.scalars().all()
        return {(r.name, r.label_id): r for r in releases}
