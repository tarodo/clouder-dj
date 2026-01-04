from pydantic import BaseModel, ConfigDict

from backend.schemas.mixins import MetaDataMixin, NoteMixin


class LabelBase(BaseModel):
    name: str
    code: str | None = None


class LabelCreate(LabelBase, NoteMixin):
    pass


class LabelUpdate(NoteMixin):
    name: str | None = None
    code: str | None = None


class LabelRead(LabelBase, MetaDataMixin):
    model_config = ConfigDict(from_attributes=True)

