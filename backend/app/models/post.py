from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Post(Base):
    """Publicación capturada desde la Graph API (post, foto, video o live)."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pages.id"), nullable=False)
    platform_post_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # status | photo | video | live
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    permalink: Mapped[str | None] = mapped_column(String, nullable=True)
    media_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    live_status: Mapped[str | None] = mapped_column(String, nullable=True)  # LIVE | VOD | null
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page: Mapped["Page"] = relationship(back_populates="posts")
    detections: Mapped[list["Detection"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    embedding: Mapped["PostEmbedding"] = relationship(back_populates="post", cascade="all, delete-orphan", uselist=False)
    alerts: Mapped[list["Alert"]] = relationship(back_populates="post", cascade="all, delete-orphan")
