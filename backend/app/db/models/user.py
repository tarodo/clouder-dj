from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .spotify_token import SpotifyToken
    from .category import Category
    from .raw_layer import RawLayerBlock


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    spotify_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    spotify_token: Mapped["SpotifyToken"] = relationship(
        "SpotifyToken",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    raw_layer_blocks: Mapped[List["RawLayerBlock"]] = relationship(
        "RawLayerBlock",
        back_populates="user",
        cascade="all, delete-orphan",
    )
