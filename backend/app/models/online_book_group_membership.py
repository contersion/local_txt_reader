from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint

from app.core.database import Base


online_book_group_memberships = Table(
    "online_book_group_memberships",
    Base.metadata,
    Column("online_book_id", ForeignKey("online_shelf_books.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("group_id", ForeignKey("book_groups.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    UniqueConstraint("online_book_id", "group_id", name="uq_online_book_group_memberships_book_group"),
)
