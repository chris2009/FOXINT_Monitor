from pydantic import BaseModel

from app.schemas.post import PostRead


class FaceSearchResult(BaseModel):
    post: PostRead
    image_url: str
    bbox: list[float] | None
    score: float  # similitud coseno (1 - distancia); mayor = cara más parecida
