from typing import List, Tuple

from sqlalchemy import Integer, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from app.db.models.external_data import (
    ExternalData,
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.models.style import Style
from app.repositories.base import BaseRepository


class StyleRepository(BaseRepository[Style]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Style, db=db)

    async def get(self, *, id: int) -> Style | None:
        result = await self.db.execute(select(Style).filter(Style.id == id))
        return result.scalars().first()

    async def get_styles_with_track_counts(self) -> List[Tuple[Style, int]]:
        stmt = (
            select(Style, func.count(ExternalData.entity_id))
            .outerjoin(
                ExternalData,
                and_(
                    ExternalData.provider == ExternalDataProvider.BEATPORT,
                    ExternalData.entity_type == ExternalDataEntityType.TRACK,
                    cast(ExternalData.raw_data["genre"]["id"].astext, Integer)
                    == Style.beatport_style_id,
                ),
            )
            .group_by(Style.id)
            .order_by(Style.name)
        )
        result: Result[Tuple[Style, int]] = await self.db.execute(stmt)
        rows = list(result.all())
        return [(row[0], row[1]) for row in rows]
