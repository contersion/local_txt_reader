from datetime import datetime

from pydantic import Field

from app.schemas.book_group import BookGroupSummary
from app.schemas.common import ORMModel


class OnlineBookAddRequest(ORMModel):
    source_id: int = Field(ge=1)
    detail_url: str = Field(min_length=1, max_length=2000)
    remote_book_id: str | None = Field(default=None, max_length=255)


class OnlineBookRead(ORMModel):
    id: int
    user_id: int
    source_id: int
    source_name: str
    title: str
    author: str | None = None
    cover_url: str | None = None
    description: str | None = None
    remote_book_id: str | None = None
    detail_url: str
    total_chapters: int | None = None
    latest_catalog_fetched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    groups: list[BookGroupSummary] = Field(default_factory=list)


class OnlineCatalogEntryRead(ORMModel):
    id: int
    online_book_id: int
    chapter_index: int
    chapter_title: str
    chapter_url: str
    created_at: datetime
    updated_at: datetime


class OnlineChapterContentRead(ORMModel):
    online_book_id: int
    chapter_index: int
    chapter_title: str
    content: str
    content_length: int
    source_url: str | None = None


class OnlineReadingProgressSyncRequest(ORMModel):
    chapter_index: int = Field(default=0, ge=0)
    char_offset: int = Field(default=0, ge=0)
    percent: float = Field(default=0.0, ge=0.0, le=100.0)
    updated_at: datetime


class OnlineReadingProgressRead(ORMModel):
    id: int
    user_id: int
    online_book_id: int
    chapter_index: int
    char_offset: int
    percent: float
    updated_at: datetime
