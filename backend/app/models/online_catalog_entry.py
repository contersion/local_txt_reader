from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class OnlineCatalogEntry(Base):
    __tablename__ = "online_catalog_entries"
    __table_args__ = (UniqueConstraint("online_book_id", "chapter_index", name="uq_online_catalog_entries_book_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    online_book_id: Mapped[int] = mapped_column(ForeignKey("online_shelf_books.id", ondelete="CASCADE"), index=True, nullable=False)
    chapter_index: Mapped[int] = mapped_column(nullable=False)
    chapter_title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    online_book: Mapped["OnlineShelfBook"] = relationship(back_populates="catalog_entries")
