from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class BookGroup(Base):
    __tablename__ = "book_groups"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_book_groups_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="book_groups")
    books: Mapped[list["Book"]] = relationship(
        secondary="book_group_memberships",
        back_populates="groups",
        order_by="Book.title",
    )
    online_books: Mapped[list["OnlineShelfBook"]] = relationship(
        secondary="online_book_group_memberships",
        back_populates="groups",
        order_by="OnlineShelfBook.title",
    )

