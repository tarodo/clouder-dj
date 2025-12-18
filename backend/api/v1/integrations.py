import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_current_user, get_uow
from backend.db.uow import UnitOfWork
from backend.models import User
from backend.schemas.integration import UserIntegration, UserIntegrationCreate
from backend.services.integration_service import IntegrationService

router = APIRouter()
integration_service = IntegrationService()


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
) -> UserIntegration:
    """
    Create a new integration for the current user.
    """
    return await integration_service.create_integration(
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
) -> list[UserIntegration]:
    """
    Get all integrations for the current user.
    """
    return list(
        await integration_service.get_user_integrations(
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
) -> None:
    """
    Delete an integration.
    """
    await integration_service.delete_integration(
        uow=uow, user_id=current_user.id, integration_id=integration_id
    )
