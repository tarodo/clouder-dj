from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.mixins import MetaDataMixin


class Artist(Base, MetaDataMixin):
    __tablename__ = "artists"

    name: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return f"Artist(id={self.id}, name={self.name})"

