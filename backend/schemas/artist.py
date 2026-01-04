from pydantic import BaseModel, ConfigDict

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class ArtistBase(BaseModel):
    name: str


class ArtistCreate(ArtistBase, NoteMixin):
    pass


class ArtistUpdate(NoteMixin):
    name: str | None = None


class ArtistRead(ArtistBase, MetaDataMixin):
    model_config = ConfigDict(from_attributes=True)

