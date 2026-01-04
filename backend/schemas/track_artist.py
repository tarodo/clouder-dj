import uuid

from pydantic import BaseModel, ConfigDict

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class TrackArtistBase(BaseModel):
    artist_id: uuid.UUID
    track_id: uuid.UUID


class TrackArtistCreate(TrackArtistBase, NoteMixin):
    pass


class TrackArtistUpdate(NoteMixin):
    pass


class TrackArtistRead(TrackArtistBase, MetaDataMixin):
    model_config = ConfigDict(from_attributes=True)

