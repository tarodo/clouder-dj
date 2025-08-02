from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.db.models.external_data import ExternalDataEntityType, ExternalDataProvider


class ExternalData(BaseModel):
    id: int
    provider: ExternalDataProvider
    entity_type: ExternalDataEntityType
    entity_id: int | None
    external_id: str
    raw_data: dict | None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
