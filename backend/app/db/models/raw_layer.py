from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .category import Category
    from .style import Style
    from .track import Track
    from .user import User


class RawLayerPlaylistType(str, enum.Enum):
    INBOX_NEW = "INBOX_NEW"
    INBOX_OLD = "INBOX_OLD"
    INBOX_NOT = "INBOX_NOT"
    TRASH = "TRASH"
    TARGET = "TARGET"


class RawLayerBlockStatus(str, enum.Enum):
    NEW = "NEW"
    PROCESSED = "PROCESSED"
    DELETED = "DELETED"


raw_layer_block_tracks = Table(
    "raw_layer_block_tracks",
    Base.metadata,
    Column(
        "raw_layer_block_id",
        Integer,
        ForeignKey("raw_layer_blocks.id"),
        primary_key=True,
    ),
    Column("track_id", Integer, ForeignKey("tracks.id"), primary_key=True),
)

raw_layer_playlists_tracks = Table(
    "raw_layer_playlists_tracks",
    Base.metadata,
    Column(
        "raw_layer_playlist_id",
        Integer,
        ForeignKey("raw_layer_playlists.id"),
        primary_key=True,
    ),
    Column("track_id", Integer, ForeignKey("tracks.id"), primary_key=True),
)


class RawLayerBlock(Base, TimestampMixin):
    __tablename__ = "raw_layer_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("styles.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RawLayerBlockStatus] = mapped_column(
        ENUM(
            RawLayerBlockStatus, name="raw_layer_block_status_enum", create_type=False
        ),
        nullable=False,
        server_default=RawLayerBlockStatus.NEW.value,
    )

    user: Mapped["User"] = relationship(back_populates="raw_layer_blocks")
    style: Mapped["Style"] = relationship(back_populates="raw_layer_blocks")
    playlists: Mapped[List["RawLayerPlaylist"]] = relationship(
        "RawLayerPlaylist",
        back_populates="raw_layer_block",
        cascade="all, delete-orphan",
    )
    tracks: Mapped[List["Track"]] = relationship(
        "Track", secondary=raw_layer_block_tracks, back_populates="raw_layer_blocks"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "style_id", "name", name="uq_raw_block_user_style_name"
        ),
    )


class RawLayerPlaylist(Base, TimestampMixin):
    __tablename__ = "raw_layer_playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_layer_block_id: Mapped[int] = mapped_column(
        ForeignKey("raw_layer_blocks.id"), nullable=False
    )
    playlist_type: Mapped[RawLayerPlaylistType] = mapped_column(
        ENUM(
            RawLayerPlaylistType, name="raw_layer_playlist_type_enum", create_type=False
        ),
        nullable=False,
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    spotify_playlist_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )
    spotify_playlist_url: Mapped[str] = mapped_column(String, nullable=False)

    raw_layer_block: Mapped["RawLayerBlock"] = relationship(
        "RawLayerBlock", back_populates="playlists"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="raw_layer_playlists"
    )
    tracks: Mapped[List["Track"]] = relationship(
        "Track",
        secondary=raw_layer_playlists_tracks,
        back_populates="raw_layer_playlists",
    )
