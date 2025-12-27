import uuid
from typing import Sequence
from datetime import datetime

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

    async def update_tokens(
        self,
        db_token: UserIntegration,
        new_access_token: str,
        new_refresh_token: str,
        new_expires_at: datetime,
        scope: str | None = None,
    ) -> UserIntegration:
        """Update access and refresh tokens."""
        db_token.access_token = new_access_token
        db_token.refresh_token = new_refresh_token
        db_token.expires_at = new_expires_at
        if scope:
            db_token.scope = scope
        return await self.update(db_obj=db_token)

    async def update_access_token(
        self,
        db_token: UserIntegration,
        new_access_token: str,
        new_expires_at: datetime,
    ) -> UserIntegration:
        """Update only access token."""
        db_token.access_token = new_access_token
        db_token.expires_at = new_expires_at
        return await self.update(db_obj=db_token)
