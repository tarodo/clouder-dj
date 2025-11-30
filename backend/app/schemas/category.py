from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str


# For API request
class CategoryCreate(CategoryBase):
    is_public: bool = False


class CategoryTrackAdd(BaseModel):
    track_uri: str


# For internal service/repository use
class CategoryCreateInternal(CategoryBase):
    user_id: int
    style_id: int
    spotify_playlist_id: str
    spotify_playlist_url: str


class CategoryUpdate(BaseModel):
    name: str


# For API response after creation
class CategoryCreateResponse(CategoryBase):
    id: int
    spotify_playlist_id: str
    spotify_playlist_url: str

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryBase):
    id: int
    user_id: int
    style_id: int
    spotify_playlist_id: str
    spotify_playlist_url: str

    model_config = ConfigDict(from_attributes=True)


class CategoryWithStyle(Category):
    style_name: str
