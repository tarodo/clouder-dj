import math
import uuid

from backend.core import errors
from backend.core.exceptions import AppException
from backend.core.security import get_password_hash, verify_password
from backend.db.uow import UnitOfWork
from backend.models import User
from backend.schemas.pagination import Page
from backend.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserAdminUpdate,
    UserAdminRead,
)


class UserService:
    """
    Service for user-related business logic.
    """

    async def create_user(
        self, uow: UnitOfWork, user_in: UserCreate, creator_id: uuid.UUID
    ) -> UserRead:
        """
        Create a new user.
        """
        user_data = user_in.model_dump(exclude={"password"})
        hashed_password = get_password_hash(user_in.password)

        async with uow:
            if await uow.users.get_by_email(user_in.email):
                raise AppException(errors.USER_ALREADY_EXISTS)

            db_user = User(
                **user_data,
                hashed_password=hashed_password,
                created_by=creator_id,
                updated_by=creator_id,
            )
            db_user = await uow.users.create(obj_in=db_user)
            return UserRead.model_validate(db_user)

    async def update_password(
        self, uow: UnitOfWork, user_id: uuid.UUID, password: str, editor_id: uuid.UUID
    ) -> None:
        """
        Update user password.
        """
        hashed_password = get_password_hash(password)
        async with uow:
            db_user = await uow.users.get(user_id)
            if not db_user:
                raise AppException(errors.USER_NOT_FOUND)

            db_user.hashed_password = hashed_password
            db_user.updated_by = editor_id
            await uow.users.update(db_obj=db_user)

    async def _update_user(
        self,
        uow: UnitOfWork,
        user_id: uuid.UUID,
        user_in: UserUpdate | UserAdminUpdate,
        editor_id: uuid.UUID,
    ) -> User:
        """
        Internal method to update a user. Returns DB object.
        """
        async with uow:
            db_user = await uow.users.get(user_id)
            if not db_user:
                raise AppException(errors.USER_NOT_FOUND)

            if user_in.email and user_in.email != db_user.email:
                existing_user = await uow.users.get_by_email(user_in.email)
                if existing_user:
                    raise AppException(errors.USER_ALREADY_EXISTS)

            update_data = user_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)

            db_user.updated_by = editor_id
            db_user = await uow.users.update(db_obj=db_user)
            return db_user

    async def update_user(
        self,
        uow: UnitOfWork,
        user_id: uuid.UUID,
        user_in: UserUpdate,
        editor_id: uuid.UUID,
    ) -> UserRead:
        """
        Update a user. Returns UserRead.
        """
        db_user = await self._update_user(
            uow=uow, user_id=user_id, user_in=user_in, editor_id=editor_id
        )
        return UserRead.model_validate(db_user)

    async def update_user_admin(
        self,
        uow: UnitOfWork,
        user_id: uuid.UUID,
        user_in: UserAdminUpdate,
        editor_id: uuid.UUID,
    ) -> UserAdminRead:
        """
        Update a user (admin). Returns UserAdminRead.
        """
        db_user = await self._update_user(
            uow=uow, user_id=user_id, user_in=user_in, editor_id=editor_id
        )
        return UserAdminRead.model_validate(db_user)

    async def get_user(self, uow: UnitOfWork, user_id: uuid.UUID) -> UserRead:
        """
        Get a user by ID.
        """
        async with uow:
            db_user = await uow.users.get(user_id)
            if not db_user:
                raise AppException(errors.USER_NOT_FOUND)
            # Convert to Pydantic schema while session is still active
            return UserRead.model_validate(db_user)

    async def get_user_admin(
        self, uow: UnitOfWork, user_id: uuid.UUID
    ) -> UserAdminRead:
        """
        Get a user by ID.
        """
        async with uow:
            db_user = await uow.users.get(user_id)
            if not db_user:
                raise AppException(errors.USER_NOT_FOUND)
            # Convert to Pydantic schema while session is still active
            return UserAdminRead.model_validate(db_user)

    async def get_users_paginated(
        self, uow: UnitOfWork, *, page: int, size: int
    ) -> Page[UserRead]:
        """
        Get a paginated list of users.
        """
        skip = (page - 1) * size
        async with uow:
            items, total = await uow.users.get_multi_paginated(skip=skip, limit=size)
            pages = math.ceil(total / size) if size > 0 else 0

            return Page[UserRead](
                items=[UserRead.model_validate(item) for item in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    async def ensure_initial_superuser(
        self,
        uow: UnitOfWork,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> UserAdminRead:
        """
        Ensure the initial superuser exists, creating or upgrading as needed.
        """
        async with uow:
            db_user = await uow.users.get_by_email(email=email)
            if db_user:
                updated = False
                if not db_user.is_superuser:
                    db_user.is_superuser = True
                    updated = True
                if not db_user.is_active:
                    db_user.is_active = True
                    updated = True
                if full_name and full_name != db_user.full_name:
                    db_user.full_name = full_name
                    updated = True
                if not verify_password(password, db_user.hashed_password):
                    db_user.hashed_password = get_password_hash(password)
                    updated = True

                if updated:
                    db_user.updated_by = db_user.id
                    db_user = await uow.users.update(db_obj=db_user)
                return UserAdminRead.model_validate(db_user)

            hashed_password = get_password_hash(password)
            superuser_id = uuid.uuid4()
            superuser = User(
                id=superuser_id,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True,
                is_superuser=True,
            )
            superuser.created_by = superuser_id
            superuser.updated_by = superuser_id
            superuser = await uow.users.create(obj_in=superuser)
            return UserAdminRead.model_validate(superuser)
