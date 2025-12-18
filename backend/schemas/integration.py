import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.integration import IntegrationProvider


class UserIntegrationBase(BaseModel):
    provider: IntegrationProvider
    external_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime | None = None
    scope: str | None = None
    token_type: str = "Bearer"


class UserIntegrationCreate(UserIntegrationBase):
    pass


class UserIntegrationUpdate(UserIntegrationBase):
    pass


class UserIntegrationInDBBase(UserIntegrationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserIntegration(UserIntegrationInDBBase):
    pass


class UserIntegrationInDB(UserIntegrationInDBBase):
    pass
