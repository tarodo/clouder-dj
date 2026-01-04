import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class TrackArtist(Base, MetaDataMixin):
    __tablename__ = "track_artists"

    artist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("artist_id", "track_id", name="uq_track_artist_pair"),
    )

    def __repr__(self) -> str:
        return f"TrackArtist(id={self.id}, artist_id={self.artist_id}, track_id={self.track_id})"

