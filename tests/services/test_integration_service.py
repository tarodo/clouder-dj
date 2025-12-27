import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.integration import UserIntegration, IntegrationProvider
from backend.schemas.integration import UserIntegrationCreate, UserIntegration as UserIntegrationSchema
from backend.services.integration_service import IntegrationService


class _MockIntegrations:
    def __init__(self) -> None:
        self.get_by_provider_and_external_id: AsyncMock = AsyncMock()
        self.create: AsyncMock = AsyncMock()
        self.get_all_by_user: AsyncMock = AsyncMock()
        self.get: AsyncMock = AsyncMock()
        self.delete: AsyncMock = AsyncMock()


class _MockUnitOfWork:
    def __init__(self) -> None:
        self.integrations = _MockIntegrations()

    async def __aenter__(self) -> "_MockUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


@pytest.fixture
def mock_uow() -> _MockUnitOfWork:
    return _MockUnitOfWork()


@pytest.fixture
def integration_service() -> IntegrationService:
    return IntegrationService()


@pytest.mark.asyncio
@patch("backend.services.integration_service.encrypt_token", side_effect=lambda x: f"encrypted_{x}")
async def test_create_integration(
    mock_encrypt: MagicMock,
    integration_service: IntegrationService,
    mock_uow: AsyncMock,
):
    """Test creation of integration with encryption."""
    user_id = uuid.uuid4()
    integration_in = UserIntegrationCreate(
        provider=IntegrationProvider.SPOTIFY,
        external_id="ext_123",
        access_token="raw_access",
        refresh_token="raw_refresh",
    )

    # Mock DB return
    db_integration = UserIntegration(
        id=uuid.uuid4(),
        user_id=user_id,
        provider=integration_in.provider,
        external_id=integration_in.external_id,
        access_token="encrypted_raw_access",
        refresh_token="encrypted_raw_refresh",
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    mock_uow.integrations.get_by_provider_and_external_id.return_value = None
    mock_uow.integrations.create.return_value = db_integration

    result = await integration_service.create_integration(mock_uow, user_id, integration_in)

    assert isinstance(result, UserIntegrationSchema)
    assert result.access_token == "encrypted_raw_access"
    mock_uow.integrations.create.assert_awaited_once()
    
    # Verify encryption was called
    assert mock_encrypt.call_count == 2


@pytest.mark.asyncio
async def test_get_user_integrations(
    integration_service: IntegrationService,
    mock_uow: AsyncMock,
):
    """Test retrieving user integrations."""
    user_id = uuid.uuid4()
    db_integration = UserIntegration(
        id=uuid.uuid4(), user_id=user_id, provider=IntegrationProvider.SPOTIFY,
        external_id="e", access_token="a", refresh_token="r", created_at=MagicMock(), updated_at=MagicMock()
    )
    mock_uow.integrations.get_all_by_user.return_value = [db_integration]

    results = await integration_service.get_user_integrations(mock_uow, user_id)

    assert len(results) == 1
    assert isinstance(results[0], UserIntegrationSchema)
