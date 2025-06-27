from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import bindparam, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

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

    async def count_unprocessed_beatport_tracks(self) -> int:
        stmt = select(func.count(ExternalData.id)).where(
            ExternalData.provider == ExternalDataProvider.BEATPORT,
            ExternalData.entity_type == ExternalDataEntityType.TRACK,
            ExternalData.entity_id.is_(None),
        )
        result = await self.db.execute(stmt)
        count = result.scalar_one_or_none()
        if count is None:
            return 0
        return count

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

    async def bulk_upsert(self, records_data: List[Dict[str, Any]]) -> None:
        """
        Efficiently bulk inserts or updates ExternalData records.

        On conflict with the unique constraint on (provider, entity_type, external_id),
        it updates the raw_data and updated_at fields. It also updates the entity_id
        if a new non-null value is provided, without overwriting an existing one
        with NULL.
        """
        if not records_data:
            return

        stmt = insert(ExternalData).values(records_data)
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_external_data_provider_entity_external_id",
            set_={
                "raw_data": stmt.excluded.raw_data,
                "entity_id": func.coalesce(
                    stmt.excluded.entity_id, ExternalData.entity_id
                ),
                "updated_at": func.now(),
            },
        )
        await self.db.execute(upsert_stmt)
