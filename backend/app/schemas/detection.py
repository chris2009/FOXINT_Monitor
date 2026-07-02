from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    analyzer: str
    result: dict[str, Any]
    score: float | None
    created_at: datetime
