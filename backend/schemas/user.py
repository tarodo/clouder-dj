from pydantic import BaseModel, ConfigDict, EmailStr

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase, NoteMixin):
    """Schema for user creation."""

    password: str


class UserUpdate(NoteMixin):
    """Schema for user update."""

    email: EmailStr | None = None
    full_name: str | None = None


class UserAdminUpdate(UserUpdate, NoteMixin):
    """Schema for user update by admin."""

    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPasswordUpdate(BaseModel):
    """Schema for password update."""

    password: str


class UserRead(UserBase):
    """Schema for reading user data."""

    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserAdminRead(UserRead, MetaDataMixin):
    """Schema for reading user data by admin."""

    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)
