from pydantic import BaseModel, ConfigDict


class Release(BaseModel):
    id: int
    name: str
    label_id: int | None

    model_config = ConfigDict(from_attributes=True)
