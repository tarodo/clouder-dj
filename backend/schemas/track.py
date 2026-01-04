import uuid

from pydantic import BaseModel, ConfigDict

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class TrackBase(BaseModel):
    name: str
    isrc: str | None = None
    duration_ms: int | None = None
    bpm: float | None = None
    key: str | None = None
    release_id: uuid.UUID | None = None


class TrackCreate(TrackBase, NoteMixin):
    pass


class TrackUpdate(NoteMixin):
    name: str | None = None
    isrc: str | None = None
    duration_ms: int | None = None
    bpm: float | None = None
    key: str | None = None
    release_id: uuid.UUID | None = None


class TrackRead(TrackBase, MetaDataMixin):
    model_config = ConfigDict(from_attributes=True)

