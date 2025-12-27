import uuid
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models import User
from backend.models.integration import IntegrationProvider


@pytest.mark.asyncio
class TestIntegrationAPI:
    """
    Tests for the Integration API endpoints.
    """

    @pytest.fixture
    async def async_client(self) -> AsyncGenerator[AsyncClient, None]:
        """Async client for making API requests."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    @pytest.fixture
    async def normal_user_token_headers(
        self, async_client: AsyncClient, normal_user: User
    ) -> dict[str, str]:
        """Fixture for authentication headers for a normal user."""
        login_data = {"username": normal_user.email, "password": "password123"}
        r = await async_client.post("/api/v1/login/", data=login_data)
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_create_integration_success(
        self,
        async_client: AsyncClient,
        normal_user_token_headers: dict,
    ):
        """Test creating an integration successfully."""
        integration_data = {
            "provider": IntegrationProvider.SPOTIFY.value,
            "external_id": "spotify_user_123",
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
            "token_type": "Bearer",
        }

        response = await async_client.post(
            "/api/v1/integrations/",
            json=integration_data,
            headers=normal_user_token_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == integration_data["provider"]
        assert data["external_id"] == integration_data["external_id"]
        assert "id" in data

    async def test_get_user_integrations(
        self,
        async_client: AsyncClient,
        normal_user_token_headers: dict,
    ):
        """Test getting user integrations."""
        # First create one
        integration_data = {
            "provider": IntegrationProvider.DEEZER.value,
            "external_id": "deezer_user_456",
            "access_token": "at",
            "refresh_token": "rt",
        }
        await async_client.post(
            "/api/v1/integrations/",
            json=integration_data,
            headers=normal_user_token_headers,
        )

        response = await async_client.get(
            "/api/v1/integrations/", headers=normal_user_token_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["provider"] == integration_data["provider"]

    async def test_delete_integration(
        self,
        async_client: AsyncClient,
        normal_user_token_headers: dict,
    ):
        """Test deleting an integration."""
        # Create
        create_resp = await async_client.post(
            "/api/v1/integrations/",
            json={"provider": "tidal", "external_id": "t1", "access_token": "a", "refresh_token": "r"},
            headers=normal_user_token_headers,
        )
        integration_id = create_resp.json()["id"]

        # Delete
        del_resp = await async_client.delete(
            f"/api/v1/integrations/{integration_id}", headers=normal_user_token_headers
        )
        assert del_resp.status_code == 204
