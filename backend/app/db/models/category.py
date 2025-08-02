from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .style import Style
    from .raw_layer import RawLayerPlaylist


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("styles.id"), nullable=False)

    spotify_playlist_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )
    spotify_playlist_url: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship(back_populates="categories")
    style: Mapped["Style"] = relationship(back_populates="categories")
    raw_layer_playlists: Mapped[List["RawLayerPlaylist"]] = relationship(
        "RawLayerPlaylist", back_populates="category"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "style_id", "name", name="uq_category_user_style_name"
        ),
    )
