from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .category import Category
    from .raw_layer import RawLayerBlock


class Style(Base, TimestampMixin):
    __tablename__ = "styles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    beatport_style_id: Mapped[Optional[int]] = mapped_column(
        Integer, unique=True, nullable=True
    )

    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="style", cascade="all, delete-orphan"
    )
    raw_layer_blocks: Mapped[List["RawLayerBlock"]] = relationship(
        "RawLayerBlock",
        back_populates="style",
        cascade="all, delete-orphan",
    )
