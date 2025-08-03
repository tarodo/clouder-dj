from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.track import Track


class ReleasePlaylistTrack(BaseModel):
    position: int
    track: Track

    model_config = ConfigDict(from_attributes=True)


class ReleasePlaylistBase(BaseModel):
    name: str
    description: str | None = None


class ReleasePlaylistCreate(ReleasePlaylistBase):
    pass


class ReleasePlaylistImport(BaseModel):
    spotify_playlist_id_or_url: str


class ReleasePlaylist(ReleasePlaylistBase):
    id: int
    user_id: int
    spotify_playlist_id: str | None = None
    spotify_playlist_url: str | None = None
    tracks: list[ReleasePlaylistTrack] = []

    model_config = ConfigDict(from_attributes=True)


class ReleasePlaylistSimple(ReleasePlaylistBase):
    id: int
    user_id: int
    spotify_playlist_id: str | None = None
    spotify_playlist_url: str | None = None
    # No tracks for list view

    model_config = ConfigDict(from_attributes=True)
