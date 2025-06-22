from datetime import date

from pydantic import BaseModel


class BeatportCollectionRequest(BaseModel):
    bp_token: str
    style_id: int
    date_from: date
    date_to: date
