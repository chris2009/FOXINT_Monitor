from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_id: int
    platform_post_id: str
    type: str
    message: str | None
    permalink: str | None
    media_urls: list | None
    is_live: bool
    live_status: str | None
    published_at: datetime | None
    captured_at: datetime
