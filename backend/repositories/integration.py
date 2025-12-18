import uuid
from typing import Sequence

from sqlalchemy import select

from backend.models.integration import IntegrationProvider, UserIntegration
from backend.repositories.base import BaseRepository


class IntegrationRepository(BaseRepository[UserIntegration]):
    model = UserIntegration

    async def get_by_provider_and_external_id(
        self, provider: IntegrationProvider, external_id: str
    ) -> UserIntegration | None:
        """
        Get an integration by provider and external ID.
        """
        query = select(self.model).where(
            self.model.provider == provider, self.model.external_id == external_id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_by_user(self, user_id: uuid.UUID) -> Sequence[UserIntegration]:
        """
        Get all integrations for a user.
        """
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
