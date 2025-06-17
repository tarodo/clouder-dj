from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .label import Label
    from .track import Track


class Release(Base, TimestampMixin):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=True)
    label_id: Mapped[int | None] = mapped_column(ForeignKey("labels.id"), nullable=True)

    label: Mapped[Label | None] = relationship("Label", back_populates="releases")
    tracks: Mapped[List["Track"]] = relationship("Track", back_populates="release")
