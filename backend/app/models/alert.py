from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    """Alerta emitida hacia un canal (telegram, email) por una regla disparada."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), nullable=False)
    # Nullable: las alertas de LiveDetector no están atadas a una keyword_rule.
    rule_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("keyword_rules.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="sent")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["Post"] = relationship(back_populates="alerts")
    rule: Mapped["KeywordRule | None"] = relationship(back_populates="alerts")
