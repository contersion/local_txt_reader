from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferences_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reading_progresses: Mapped[list["ReadingProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chapter_rules: Mapped[list["ChapterRule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    book_groups: Mapped[list["BookGroup"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

