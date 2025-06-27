from __future__ import annotations

from typing import List

from sqlalchemy import bindparam, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.external_data import (
    ExternalData,
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.repositories.base import BaseRepository


class ExternalDataRepository(BaseRepository[ExternalData]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=ExternalData, db=db)

    async def get_unprocessed_beatport_tracks(
        self, *, limit: int
    ) -> List[ExternalData]:
        stmt = (
            select(ExternalData)
            .where(
                ExternalData.provider == ExternalDataProvider.BEATPORT,
                ExternalData.entity_type == ExternalDataEntityType.TRACK,
                ExternalData.entity_id.is_(None),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def bulk_update_entity_ids(self, updates: dict[str, int]) -> None:
        """
        Bulk update entity_id for ExternalData records.
        `updates` is a mapping of external_id to entity_id (track.id).
        """
        if not updates:
            return

        update_mappings = [
            {"external_id_val": ext_id, "entity_id_val": ent_id}
            for ext_id, ent_id in updates.items()
        ]

        stmt = (
            update(ExternalData.__table__)  # type: ignore[arg-type]
            .where(ExternalData.__table__.c.external_id == bindparam("external_id_val"))
            .values(entity_id=bindparam("entity_id_val"))
        )
        await self.db.execute(stmt, update_mappings)
