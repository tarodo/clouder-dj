import uuid

from pydantic import BaseModel, ConfigDict

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class ReleaseBase(BaseModel):
    name: str
    code: str | None = None
    label_id: uuid.UUID | None = None


class ReleaseCreate(ReleaseBase, NoteMixin):
    pass


class ReleaseUpdate(NoteMixin):
    name: str | None = None
    code: str | None = None
    label_id: uuid.UUID | None = None


class ReleaseRead(ReleaseBase, MetaDataMixin):
    model_config = ConfigDict(from_attributes=True)

