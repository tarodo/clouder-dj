from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .artist import Artist
    from .external_data import ExternalData
    from .release import Release
    from .raw_layer import RawLayerBlock, RawLayerPlaylist


track_artists = Table(
    "track_artists",
    Base.metadata,
    Column("track_id", Integer, ForeignKey("tracks.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artists.id"), primary_key=True),
)


class Track(Base, TimestampMixin):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    isrc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"), nullable=False)

    release: Mapped["Release"] = relationship("Release", back_populates="tracks")
    artists: Mapped[List["Artist"]] = relationship(
        "Artist", secondary=track_artists, back_populates="tracks"
    )
    raw_layer_blocks: Mapped[List["RawLayerBlock"]] = relationship(
        "RawLayerBlock",
        secondary="raw_layer_block_tracks",
        back_populates="tracks",
    )
    raw_layer_playlists: Mapped[List["RawLayerPlaylist"]] = relationship(
        "RawLayerPlaylist",
        secondary="raw_layer_playlists_tracks",
        back_populates="tracks",
    )
    external_data: Mapped[List["ExternalData"]] = relationship(
        "ExternalData",
        primaryjoin="and_(Track.id == ExternalData.entity_id, "
        "ExternalData.entity_type == 'TRACK')",
        foreign_keys="ExternalData.entity_id",
        viewonly=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "name", "release_id", "isrc", name="uq_track_name_release_id_isrc"
        ),
    )
