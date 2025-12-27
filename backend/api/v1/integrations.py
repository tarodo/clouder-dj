import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_current_user, get_uow, oauth2_scheme
from backend.db.uow import UnitOfWork
from backend.models import User
from backend.schemas.integration import UserIntegration, UserIntegrationCreate, SpotifyAuthUrl
from backend.services.integration_service import IntegrationService

router = APIRouter()


@router.post(
    "/",
    response_model=UserIntegration,
    status_code=status.HTTP_201_CREATED,
    summary="Create integration",
)
async def create_integration(
    integration_in: UserIntegrationCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: IntegrationService = Depends(IntegrationService),
) -> UserIntegration:
    """
    Create a new integration for the current user.
    """
    return await service.create_integration(
        uow=uow, user_id=current_user.id, integration_in=integration_in
    )


@router.get(
    "/",
    response_model=list[UserIntegration],
    summary="Get user integrations",
)
async def get_user_integrations(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: IntegrationService = Depends(IntegrationService),
) -> list[UserIntegration]:
    """
    Get all integrations for the current user.
    """
    return list(
        await service.get_user_integrations(
            uow=uow, user_id=current_user.id
        )
    )


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete integration",
)
async def delete_integration(
    integration_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: IntegrationService = Depends(IntegrationService),
) -> None:
    """
    Delete an integration.
    """
    await service.delete_integration(
        uow=uow, user_id=current_user.id, integration_id=integration_id
    )


@router.get(
    "/spotify/url",
    response_model=SpotifyAuthUrl,
    summary="Get Spotify Auth URL",
)
async def get_spotify_auth_url(
    service: IntegrationService = Depends(IntegrationService),
    token: str = Depends(oauth2_scheme),
) -> SpotifyAuthUrl:
    """
    Get the URL to redirect the user to for Spotify authentication.
    """
    return SpotifyAuthUrl(url=service.get_spotify_auth_url(state=token))


@router.get(
    "/spotify/callback",
    response_model=UserIntegration,
    summary="Handle Spotify Callback",
)
async def spotify_callback(
    code: str,
    state: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    service: IntegrationService = Depends(IntegrationService),
) -> UserIntegration:
    """
    Exchange the authorization code for tokens and link the Spotify account.
    """
    current_user = await get_current_user(token=state, uow=uow)
    return await service.link_spotify_account(
        uow=uow, user_id=current_user.id, code=code
    )

