from backend.core.exceptions import AppException
import uuid

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import (
    PaginationParams,
    get_current_user,
    get_current_superuser,
    get_pagination_params,
    get_uow,
)
from backend.core.errors import (
    FORBIDDEN,
    UNAUTHORIZED,
    USER_ALREADY_EXISTS,
    USER_NOT_FOUND,
    build_error_responses,
)
from backend.db.uow import UnitOfWork
from backend.models import User
from backend.schemas.pagination import Page
from backend.schemas.user import (
    UserCreate,
    UserPasswordUpdate,
    UserRead,
    UserUpdate,
    UserAdminUpdate,
    UserAdminRead,
)
from backend.services.user import UserService

router = APIRouter()


@router.get(
    "/",
    response_model=Page[UserRead],
    summary="Get all users (paginated)",
    dependencies=[Depends(get_current_superuser)],
    responses={
        **build_error_responses(UNAUTHORIZED, FORBIDDEN),
    },
)
async def get_all_users(
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> Page[UserRead]:
    """
    Get a paginated list of all users. Requires superuser privileges.
    """
    return await user_service.get_users_paginated(
        uow=uow, page=pagination.page, size=pagination.size
    )


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin only)",
    responses={
        **build_error_responses(USER_ALREADY_EXISTS, UNAUTHORIZED, FORBIDDEN),
    },
)
async def create_user(
    user_in: UserCreate,
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    current_superuser: User = Depends(get_current_superuser),
) -> UserRead:
    """
    Create a new user. Requires superuser privileges.
    """
    creator_id = current_superuser.id
    return await user_service.create_user(
        uow=uow, user_in=user_in, creator_id=creator_id
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    responses={**build_error_responses(UNAUTHORIZED)},
)
async def get_current_user_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Get the current authenticated user's data.
    """
    return UserRead.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user",
    responses={
        **build_error_responses(UNAUTHORIZED, USER_ALREADY_EXISTS),
    },
)
async def update_user_me(
    user_in: UserUpdate,
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Update the current authenticated user's profile.
    """
    return await user_service.update_user(
        uow=uow, user_id=current_user.id, user_in=user_in, editor_id=current_user.id
    )


@router.get(
    "/{user_id}",
    response_model=UserAdminRead,
    summary="Get a user by ID",
    responses={
        **build_error_responses(USER_NOT_FOUND, UNAUTHORIZED, FORBIDDEN),
    },
)
async def get_user(
    user_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    _current_user: User = Depends(get_current_superuser),
) -> UserAdminRead:
    """
    Get a user by their ID. Requires superuser privileges.
    """
    return await user_service.get_user_admin(uow=uow, user_id=user_id)


@router.patch(
    "/{user_id}",
    response_model=UserAdminRead,
    summary="Update a user",
    responses={
        **build_error_responses(
            USER_NOT_FOUND, UNAUTHORIZED, FORBIDDEN, USER_ALREADY_EXISTS
        ),
    },
)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserAdminUpdate,
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    current_superuser: User = Depends(get_current_superuser),
) -> UserAdminRead:
    """
    Update a user. Requires superuser privileges.
    """
    return await user_service.update_user_admin(
        uow=uow, user_id=user_id, user_in=user_in, editor_id=current_superuser.id
    )


@router.put(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user password",
    responses={
        **build_error_responses(USER_NOT_FOUND, UNAUTHORIZED, FORBIDDEN),
    },
)
async def update_user_password(
    user_id: uuid.UUID,
    user_in: UserPasswordUpdate,
    uow: UnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(UserService),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Update a user's password.
    Authenticated user can update their own password.
    Superuser can update any user's password.
    """
    if str(current_user.id) != str(user_id) and not current_user.is_superuser:
        raise AppException(FORBIDDEN)

    await user_service.update_password(
        uow=uow, user_id=user_id, password=user_in.password, editor_id=current_user.id
    )
