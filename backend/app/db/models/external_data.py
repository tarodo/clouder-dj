from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    func,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ExternalDataProvider(str, enum.Enum):
    BEATPORT = "BEATPORT"
    SPOTIFY = "SPOTIFY"
    TIDAL = "TIDAL"


class ExternalDataEntityType(str, enum.Enum):
    ARTIST = "ARTIST"
    LABEL = "LABEL"
    RELEASE = "RELEASE"
    TRACK = "TRACK"


class ExternalData(Base):
    __tablename__ = "external_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[ExternalDataProvider] = mapped_column(
        ENUM(ExternalDataProvider, name="provider_enum", create_type=True),
        nullable=False,
    )
    entity_type: Mapped[ExternalDataEntityType] = mapped_column(
        ENUM(ExternalDataEntityType, name="entity_type_enum", create_type=True),
        nullable=False,
    )
    entity_id: Mapped[int] = mapped_column(Integer, nullable=True)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "entity_type",
            "external_id",
            name="uq_external_data_provider_entity_external_id",
        ),
        Index(
            "ix_external_data_provider_entity_id",
            "provider",
            "entity_type",
            "entity_id",
        ),
    )
