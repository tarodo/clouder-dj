from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.raw_layer import RawLayerPlaylistType


class RawLayerBlockCreate(BaseModel):
    style_id: int
    block_name: str
    start_date: date
    end_date: date


class RawLayerPlaylistResponse(BaseModel):
    playlist_type: RawLayerPlaylistType = Field(..., serialization_alias="type")
    spotify_playlist_id: str
    spotify_playlist_url: str
    category_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True, use_enum_values=True, populate_by_name=True
    )


class RawLayerBlockResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    playlists: List[RawLayerPlaylistResponse]
    track_count: int

    model_config = ConfigDict(from_attributes=True)
