from pydantic import BaseModel

from app.schemas.post import PostRead


class SearchResult(BaseModel):
    post: PostRead
    score: float  # similitud coseno (1 - distancia); mayor = más relevante
