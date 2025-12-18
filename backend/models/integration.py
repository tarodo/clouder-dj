import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class IntegrationProvider(str, Enum):
    SPOTIFY = "spotify"
    DEEZER = "deezer"
    TIDAL = "tidal"


class UserIntegration(Base, MetaDataMixin):
    __tablename__ = "user_integrations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[IntegrationProvider] = mapped_column(String, nullable=False)
    external_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    scope: Mapped[str] = mapped_column(String, nullable=True)
    token_type: Mapped[str] = mapped_column(String, default="Bearer", nullable=False)

    def __repr__(self) -> str:
        return f"UserIntegration(user_id={self.user_id}, provider={self.provider}, external_id={self.external_id})"
