from __future__ import annotations

from typing import TYPE_CHECKING, List

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
    from .release import Release


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
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    key: Mapped[str | None] = mapped_column(String, nullable=True)
    isrc: Mapped[str | None] = mapped_column(String, nullable=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"), nullable=False)

    release: Mapped["Release"] = relationship("Release", back_populates="tracks")
    artists: Mapped[List["Artist"]] = relationship(
        "Artist", secondary=track_artists, back_populates="tracks"
    )

    __table_args__ = (
        UniqueConstraint(
            "name", "release_id", "isrc", name="uq_track_name_release_id_isrc"
        ),
    )
