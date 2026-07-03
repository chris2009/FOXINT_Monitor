from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

FACE_EMBEDDING_DIM = 512  # facenet InceptionResnetV1 (VGGFace2)


class PostFace(Base):
    """Una cara detectada dentro de una imagen de un post, con su embedding facial.

    Se usa SOLO para búsqueda por SIMILITUD sobre el corpus ya capturado (encontrar
    imágenes con caras parecidas entre lo que el sistema ingirió de páginas públicas
    autorizadas). NO identifica ni nombra personas, ni busca en la web abierta.
    """

    __tablename__ = "post_faces"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    face_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [x1, y1, x2, y2]
    embedding: Mapped[list[float]] = mapped_column(Vector(FACE_EMBEDDING_DIM), nullable=False)

    post: Mapped["Post"] = relationship(back_populates="faces")
