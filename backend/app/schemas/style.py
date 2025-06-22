from pydantic import BaseModel, ConfigDict


class Style(BaseModel):
    id: int
    name: str
    beatport_style_id: int | None

    model_config = ConfigDict(from_attributes=True)
