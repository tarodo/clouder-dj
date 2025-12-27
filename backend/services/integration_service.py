import uuid
from typing import Sequence

from backend.core.security import decrypt_token, encrypt_token
from backend.db.uow import UnitOfWork
from backend.models.integration import UserIntegration as UserIntegrationModel
from backend.schemas.integration import UserIntegration, UserIntegrationCreate


class IntegrationService:
    """
    Service for integration-related business logic.
    """

    async def create_integration(
        self, uow: UnitOfWork, user_id: uuid.UUID, integration_in: UserIntegrationCreate
    ) -> UserIntegration:
        """
        Create a new integration.
        """
        async with uow:
            # Check if integration already exists
            existing = await uow.integrations.get_by_provider_and_external_id(
                integration_in.provider, integration_in.external_id
            )
            # If exists and belongs to other user -> error? Or update?
            # For now, let's assume we allow re-linking or assume unique constraint handled by business logic if needed.
            # But duplicate provider+external_id should probably belong to one user.
            
            # Encrypt tokens
            encrypted_access_token = encrypt_token(integration_in.access_token)
            encrypted_refresh_token = encrypt_token(integration_in.refresh_token)

            integration = UserIntegrationModel(
                user_id=user_id,
                provider=integration_in.provider,
                external_id=integration_in.external_id,
                access_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                expires_at=integration_in.expires_at,
                scope=integration_in.scope,
                token_type=integration_in.token_type,
                created_by=user_id,
                updated_by=user_id,
            )
            integration = await uow.integrations.create(obj_in=integration)
            return UserIntegration.model_validate(integration)

    async def get_user_integrations(
        self, uow: UnitOfWork, user_id: uuid.UUID
    ) -> Sequence[UserIntegration]:
        """
        Get all integrations for a user.
        """
        async with uow:
            integrations = await uow.integrations.get_all_by_user(user_id)
            # We assume we return them as is, or maybe we want to mask tokens?
            # usually client doesn't need tokens, only status.
            # But let's return full object for now, mapped to schema in API layer.
            return [UserIntegration.model_validate(i) for i in integrations]

    async def delete_integration(
        self, uow: UnitOfWork, user_id: uuid.UUID, integration_id: uuid.UUID
    ) -> None:
        """
        Delete an integration.
        """
        async with uow:
            integration = await uow.integrations.get(integration_id)
            if integration and integration.user_id == user_id:
                await uow.integrations.delete(db_obj=integration)
