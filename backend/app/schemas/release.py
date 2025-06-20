from datetime import date

from pydantic import BaseModel, ConfigDict


class Release(BaseModel):
    id: int
    name: str
    release_date: date | None
    label_id: int | None

    model_config = ConfigDict(from_attributes=True)
