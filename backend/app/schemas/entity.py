from pydantic import BaseModel


class EntityCount(BaseModel):
    text: str
    type: str  # persona | lugar | organización | otro
    count: int
