import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class Release(Base, MetaDataMixin):
    __tablename__ = "releases"

    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str | None] = mapped_column(String, nullable=True)
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("labels.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("label_id", "code", name="uq_release_label_code"),
    )

    def __repr__(self) -> str:
        return f"Release(id={self.id}, name={self.name}, code={self.code}, label_id={self.label_id})"

