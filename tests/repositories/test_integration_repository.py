import uuid
from unittest.mock import AsyncMock, MagicMock


import pytest
from sqlalchemy import select

from backend.models.integration import UserIntegration, IntegrationProvider
from backend.repositories.integration import IntegrationRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture for a mocked AsyncSession."""
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def integration_repository(mock_session: AsyncMock) -> IntegrationRepository:
    """Fixture for IntegrationRepository."""
    return IntegrationRepository(session=mock_session)


@pytest.fixture
def test_integration() -> UserIntegration:
    """Fixture for a sample UserIntegration object."""
    return UserIntegration(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider=IntegrationProvider.SPOTIFY,
        external_id="test_ext_id",
        access_token="enc_at",
        refresh_token="enc_rt",
    )


@pytest.mark.asyncio
async def test_get_by_provider_and_external_id(
    integration_repository: IntegrationRepository,
    mock_session: AsyncMock,
    test_integration: UserIntegration,
):
    """Test getting integration by provider and external ID."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_integration
    mock_session.execute.return_value = mock_result

    result = await integration_repository.get_by_provider_and_external_id(
        IntegrationProvider.SPOTIFY, "test_ext_id"
    )

    assert result == test_integration
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_by_user(
    integration_repository: IntegrationRepository,
    mock_session: AsyncMock,
    test_integration: UserIntegration,
):
    """Test getting all integrations for a user."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [test_integration]
    mock_session.execute.return_value = mock_result

    result = await integration_repository.get_all_by_user(test_integration.user_id)

    assert result == [test_integration]
    mock_session.execute.assert_awaited_once()
