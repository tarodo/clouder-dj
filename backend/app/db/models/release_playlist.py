from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .track import Track
    from .user import User


class ReleasePlaylist(Base, TimestampMixin):
    __tablename__ = "release_playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    spotify_playlist_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True
    )
    spotify_playlist_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="release_playlists")
    tracks: Mapped[List["ReleasePlaylistTrack"]] = relationship(
        "ReleasePlaylistTrack",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="ReleasePlaylistTrack.position",
    )


class ReleasePlaylistTrack(Base):
    __tablename__ = "release_playlist_tracks"

    release_playlist_id: Mapped[int] = mapped_column(
        ForeignKey("release_playlists.id"), primary_key=True
    )
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"))
    position: Mapped[int] = mapped_column(Integer, primary_key=True)

    playlist: Mapped["ReleasePlaylist"] = relationship(
        "ReleasePlaylist", back_populates="tracks"
    )
    track: Mapped["Track"] = relationship(
        "Track", back_populates="playlist_associations"
    )

    __table_args__ = (
        UniqueConstraint(
            "release_playlist_id", "track_id", name="uq_release_playlist_track"
        ),
    )
