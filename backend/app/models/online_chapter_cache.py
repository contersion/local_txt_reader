from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class OnlineChapterCache(Base):
    __tablename__ = "online_chapter_caches"
    __table_args__ = (UniqueConstraint("online_book_id", "chapter_index", name="uq_online_chapter_caches_book_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    online_book_id: Mapped[int] = mapped_column(ForeignKey("online_shelf_books.id", ondelete="CASCADE"), index=True, nullable=False)
    chapter_index: Mapped[int] = mapped_column(nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    online_book: Mapped["OnlineShelfBook"] = relationship(back_populates="chapter_caches")
