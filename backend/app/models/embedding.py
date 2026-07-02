from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

EMBEDDING_DIM = 768  # nomic-embed-text


class PostEmbedding(Base):
    """Vector semántico de un post, para búsqueda por similitud (pgvector)."""

    __tablename__ = "post_embeddings"

    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="embedding")
