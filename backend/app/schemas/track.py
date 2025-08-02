from pydantic import BaseModel, ConfigDict

from .artist import Artist
from .external_data import ExternalData as ExternalDataSchema


class Track(BaseModel):
    id: int
    name: str
    duration_ms: int | None
    bpm: float | None
    key: str | None
    isrc: str | None
    release_id: int

    model_config = ConfigDict(from_attributes=True)


class TrackWithSpotifyData(BaseModel):
    id: int
    artists: list[Artist]
    external_data: list[ExternalDataSchema]

    model_config = ConfigDict(from_attributes=True)
