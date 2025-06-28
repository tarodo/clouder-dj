from pydantic import BaseModel, ConfigDict


class Track(BaseModel):
    id: int
    name: str
    duration_ms: int | None
    bpm: float | None
    key: str | None
    isrc: str | None
    release_id: int

    model_config = ConfigDict(from_attributes=True)
