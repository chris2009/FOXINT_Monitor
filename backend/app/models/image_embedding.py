from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

IMAGE_EMBEDDING_DIM = 512  # CLIP ViT-B/32


class PostImageEmbedding(Base):
    """Vector CLIP de una imagen de un post, para búsqueda visual (texto→imagen e imagen→imagen).

    Un post puede tener varias imágenes, por eso es una fila por imagen (no PK en post_id).
    """

    __tablename__ = "post_image_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(IMAGE_EMBEDDING_DIM), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="image_embeddings")
