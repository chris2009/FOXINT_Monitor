from sqlalchemy import ARRAY, BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KeywordRule(Base):
    """Regla de palabras clave que dispara detecciones y alertas."""

    __tablename__ = "keyword_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    match_type: Mapped[str] = mapped_column(String, nullable=False, default="any")  # any | all | phrase
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")  # low | medium | high
    notify_channels: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=["telegram"])
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    alerts: Mapped[list["Alert"]] = relationship(back_populates="rule", cascade="all, delete-orphan")
