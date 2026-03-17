from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class OnlineShelfBook(Base):
    __tablename__ = "online_shelf_books"
    __table_args__ = (UniqueConstraint("user_id", "source_id", "detail_url", name="uq_online_shelf_books_user_source_detail"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("online_sources.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_book_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    detail_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    total_chapters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latest_catalog_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    source: Mapped["OnlineSource"] = relationship(back_populates="online_books")
    catalog_entries: Mapped[list["OnlineCatalogEntry"]] = relationship(
        back_populates="online_book",
        cascade="all, delete-orphan",
        order_by="OnlineCatalogEntry.chapter_index",
    )
    chapter_caches: Mapped[list["OnlineChapterCache"]] = relationship(
        back_populates="online_book",
        cascade="all, delete-orphan",
    )
    reading_progresses: Mapped[list["OnlineReadingProgress"]] = relationship(
        back_populates="online_book",
        cascade="all, delete-orphan",
    )
    groups: Mapped[list["BookGroup"]] = relationship(
        secondary="online_book_group_memberships",
        back_populates="online_books",
        order_by="BookGroup.name",
    )
