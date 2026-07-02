from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    rule_id: int | None
    channel: str
    status: str
    sent_at: datetime
