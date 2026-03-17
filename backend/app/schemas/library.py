from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.book_group import BookGroupSummary
from app.schemas.common import ORMModel


class LibraryBookSourceMeta(ORMModel):
    source_id: int | None = None
    remote_book_id: str | None = None
    detail_url: str | None = None


class LibraryBookSummary(ORMModel):
    library_id: str
    source_kind: Literal["local", "online"]
    source_label: str
    entity_id: int
    title: str
    author: str | None = None
    cover_url: str | None = None
    total_chapters: int | None = None
    total_words: int | None = None
    progress_percent: float | None = None
    recent_read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    groups: list[BookGroupSummary] = Field(default_factory=list)
    source_meta: LibraryBookSourceMeta | None = None
