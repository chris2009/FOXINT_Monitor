from pydantic import BaseModel, ConfigDict


class KeywordRuleCreate(BaseModel):
    label: str
    keywords: list[str]
    match_type: str = "any"  # any | all | phrase
    severity: str = "medium"  # low | medium | high
    notify_channels: list[str] = ["telegram"]
    is_active: bool = True


class KeywordRuleUpdate(BaseModel):
    label: str | None = None
    keywords: list[str] | None = None
    match_type: str | None = None
    severity: str | None = None
    notify_channels: list[str] | None = None
    is_active: bool | None = None


class KeywordRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    keywords: list[str]
    match_type: str
    severity: str
    notify_channels: list[str]
    is_active: bool
