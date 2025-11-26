from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.raw_layer import RawLayerBlockStatus, RawLayerPlaylistType


class RawLayerBlockCreate(BaseModel):
    block_name: str
    start_date: date
    end_date: date


class RawLayerPlaylistResponse(BaseModel):
    playlist_type: RawLayerPlaylistType = Field(..., serialization_alias="type")
    spotify_playlist_id: str
    spotify_playlist_url: str
    category_id: int | None = None
    category_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True, use_enum_values=True, populate_by_name=True
    )


class RawLayerBlockResponse(BaseModel):
    id: int
    name: str
    status: RawLayerBlockStatus
    start_date: date
    end_date: date
    playlists: List[RawLayerPlaylistResponse]
    track_count: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class RawLayerBlockSummary(BaseModel):
    id: int
    name: str
    style_id: int
    style_name: str
    status: RawLayerBlockStatus
    start_date: date
    end_date: date
    track_count: int
    playlist_count: int
    playlists: List[RawLayerPlaylistResponse]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
