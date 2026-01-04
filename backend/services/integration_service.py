import uuid
import secrets
import hashlib
import base64
from typing import Sequence
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

import httpx

from backend.clients.spotify import SpotifyAPIClient
from backend.clients.tidal import TidalAPIClient
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
        self, uow: UnitOfWork, user_id: uuid.UUID, code: str, http_client: httpx.AsyncClient
    ) -> UserIntegration:
        """
        Exchange code for tokens and link Spotify account to user.
        """
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

    def get_tidal_auth_url(self, state: str | None = None) -> str:
        """
        Generate the TIDAL OAuth2 authorization URL.
        """
        verifier, challenge = self._generate_pkce_pair()
        encrypted_verifier = encrypt_token(verifier)

        # Combine token and encrypted verifier in state
        combined_state = f"{state}:{encrypted_verifier}" if state else encrypted_verifier

        params = {
            "client_id": settings.TIDAL_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.TIDAL_REDIRECT_URI,
            "scope": settings.TIDAL_SCOPES,
            "state": combined_state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return f"{settings.TIDAL_AUTH_URL}?{urlencode(params)}"

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generates a PKCE code verifier and code challenge.
        """
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = (
            base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")
        )
        return code_verifier, code_challenge

    async def link_tidal_account(
        self, uow: UnitOfWork, user_id: uuid.UUID, code: str, code_verifier: str, http_client: httpx.AsyncClient
    ) -> UserIntegration:
        """
        Exchange code for tokens and link TIDAL account to user.
        """
        client = TidalAPIClient(http_client)
        token_data = await client.exchange_code_for_token(code, code_verifier)

        # Try to extract user info from token response first
        external_id = None
        if "user" in token_data:
            user_data = token_data["user"]
            external_id = str(user_data.get("userId") or user_data.get("id"))
        elif "userId" in token_data:
            external_id = str(token_data["userId"])

        if not external_id:
            # Get user profile (session) to get userId
            session_data = await client.get_user_profile(token_data["access_token"])
            external_id = str(session_data["userId"])

        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).replace(tzinfo=None)
        scope = token_data.get("scope")

        encrypted_access_token = encrypt_token(access_token)
        encrypted_refresh_token = encrypt_token(refresh_token)

        async with uow:
            existing = await uow.integrations.get_by_provider_and_external_id(
                IntegrationProvider.TIDAL, external_id
            )

            if existing:
                existing.user_id = user_id
                return UserIntegration.model_validate(
                    await uow.integrations.update_tokens(
                        existing, encrypted_access_token, encrypted_refresh_token, expires_at, scope
                    )
                )
            else:
                integration = UserIntegrationModel(
                    user_id=user_id,
                    provider=IntegrationProvider.TIDAL,
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
