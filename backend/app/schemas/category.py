from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    user_id: int
    style_id: int
    spotify_playlist_id: str
    spotify_playlist_url: str


class CategoryUpdate(BaseModel):
    name: str | None = None


class Category(CategoryBase):
    id: int
    user_id: int
    style_id: int
    spotify_playlist_id: str
    spotify_playlist_url: str

    model_config = ConfigDict(from_attributes=True)
