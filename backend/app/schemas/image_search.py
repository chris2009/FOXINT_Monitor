from pydantic import BaseModel

from app.schemas.post import PostRead


class ImageSearchResult(BaseModel):
    post: PostRead
    image_url: str
    score: float  # similitud coseno (1 - distancia); mayor = más parecido
