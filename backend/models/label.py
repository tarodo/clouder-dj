from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class Label(Base, MetaDataMixin):
    __tablename__ = "labels"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

    def __repr__(self) -> str:
        return f"Label(id={self.id}, name={self.name}, code={self.code})"

