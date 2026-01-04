import uuid

from sqlalchemy import select

from backend.models.release import Release
from backend.repositories.base import BaseRepository


class ReleaseRepository(BaseRepository[Release]):
    model = Release

    async def get_by_label_and_code(
        self, label_id: uuid.UUID, code: str
    ) -> Release | None:
        """Get a release by label_id and code."""
        query = select(self.model).where(
            self.model.label_id == label_id, self.model.code == code
        )
        result = await self.session.execute(query)
        return result.scalars().first()

