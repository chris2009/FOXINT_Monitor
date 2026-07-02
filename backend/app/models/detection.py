from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Detection(Base):
    """Resultado emitido por un analizador del bus (keyword, sentiment, ner, ocr, ...)."""

    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), nullable=False)
    analyzer: Mapped[str] = mapped_column(String, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["Post"] = relationship(back_populates="detections")
