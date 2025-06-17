from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None


class UserCreate(UserBase):
    spotify_id: str


class UserUpdate(UserBase):
    pass


class User(UserBase):
    id: int
    spotify_id: str

    model_config = ConfigDict(from_attributes=True)
