from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageCreate(BaseModel):
    fb_page_id: str  # ID/handle/URL del objetivo (página de Facebook o canal de YouTube)
    platform: str = "facebook"  # facebook | youtube
    poll_interval: int = 300


class PageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fb_page_id: str
    name: str
    category: str
    platform: str
    fan_count: int | None
    followers_count: int | None
    poll_interval: int
    is_active: bool
    created_at: datetime
