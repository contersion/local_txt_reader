from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class OnlineReadingProgress(Base):
    __tablename__ = "online_reading_progress"
    __table_args__ = (UniqueConstraint("user_id", "online_book_id", name="uq_online_reading_progress_user_book"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    online_book_id: Mapped[int] = mapped_column(ForeignKey("online_shelf_books.id", ondelete="CASCADE"), index=True, nullable=False)
    chapter_index: Mapped[int] = mapped_column(default=0, nullable=False)
    char_offset: Mapped[int] = mapped_column(default=0, nullable=False)
    percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    online_book: Mapped["OnlineShelfBook"] = relationship(back_populates="reading_progresses")
