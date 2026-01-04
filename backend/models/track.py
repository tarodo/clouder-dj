import uuid

from sqlalchemy import ForeignKey, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class Track(Base, MetaDataMixin):
    __tablename__ = "tracks"

    name: Mapped[str] = mapped_column(String, nullable=False)
    isrc: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    key: Mapped[str | None] = mapped_column(String, nullable=True)
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("releases.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"Track(id={self.id}, name={self.name}, isrc={self.isrc})"

