from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.models.label import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Label, db=db)

    async def bulk_get_or_create_by_name(self, names: List[str]) -> Dict[str, Label]:
        """
        Efficiently gets or creates labels by name.
        Returns a dictionary mapping name to Label object.
        """
        if not names:
            return {}

        unique_names = sorted(list(set(names)))

        # Attempt to insert all, ignoring conflicts for existing names
        insert_stmt = insert(Label).values([{"name": name} for name in unique_names])
        on_conflict_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["name"])
        await self.db.execute(on_conflict_stmt)

        # Fetch all required labels (both existing and newly created)
        select_stmt = select(Label).where(Label.name.in_(unique_names))
        result = await self.db.execute(select_stmt)
        labels = result.scalars().all()

        return {label.name: label for label in labels}
