import uuid
from typing import Sequence
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

import httpx

from backend.clients.spotify import SpotifyAPIClient
from backend.core.settings import settings
from backend.core.security import decrypt_token, encrypt_token
from backend.db.uow import UnitOfWork
from backend.models.integration import UserIntegration as UserIntegrationModel, IntegrationProvider
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

    def get_spotify_auth_url(self, state: str | None = None) -> str:
        """
        Generate the Spotify OAuth2 authorization URL.
        """
        params = {
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "scope": settings.SPOTIFY_SCOPES,
            "state": state,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return f"{settings.SPOTIFY_AUTH_URL}?{urlencode(params)}"

    async def link_spotify_account(
        self, uow: UnitOfWork, user_id: uuid.UUID, code: str
    ) -> UserIntegration:
        """
        Exchange code for tokens and link Spotify account to user.
        """
        async with httpx.AsyncClient() as http_client:
            client = SpotifyAPIClient(http_client)
            token_data = await client.exchange_code_for_token(code)
            
            # Get user profile to identify the account
            profile = await client.get_user_profile(token_data["access_token"])
            external_id = profile["id"]

            # Prepare token data
            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).replace(tzinfo=None)
            scope = token_data.get("scope")

            # Encrypt tokens
            encrypted_access_token = encrypt_token(access_token)
            encrypted_refresh_token = encrypt_token(refresh_token)

            async with uow:
                # Check if integration exists
                existing = await uow.integrations.get_by_provider_and_external_id(
                    IntegrationProvider.SPOTIFY, external_id
                )

                if existing:
                    # Update existing integration
                    # Ensure it belongs to the current user (or handle account merging/stealing logic)
                    # For now, we update the tokens and ensure user_id matches
                    existing.user_id = user_id # Re-link if needed
                    return UserIntegration.model_validate(
                        await uow.integrations.update_tokens(
                            existing, encrypted_access_token, encrypted_refresh_token, expires_at, scope
                        )
                    )
                else:
                    # Create new integration
                    integration = UserIntegrationModel(
                        user_id=user_id,
                        provider=IntegrationProvider.SPOTIFY,
                        external_id=external_id,
                        access_token=encrypted_access_token,
                        refresh_token=encrypted_refresh_token,
                        expires_at=expires_at,
                        scope=scope,
                        token_type="Bearer",
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    created = await uow.integrations.create(obj_in=integration)
                    return UserIntegration.model_validate(created)
