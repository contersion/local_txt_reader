from typing import Literal

from pydantic import Field

from app.schemas.common import ORMModel


class OnlineDiscoverySearchRequest(ORMModel):
    source_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=200)
    page: int = Field(default=1, ge=1)


class OnlineDiscoveryDetailRequest(ORMModel):
    source_id: int = Field(ge=1)
    detail_url: str = Field(min_length=1, max_length=2000)
    remote_book_id: str | None = Field(default=None, max_length=255)


class OnlineDiscoveryCatalogRequest(ORMModel):
    source_id: int = Field(ge=1)
    catalog_url: str = Field(min_length=1, max_length=2000)


class OnlineDiscoveryChapterRequest(ORMModel):
    source_id: int = Field(ge=1)
    chapter_url: str = Field(min_length=1, max_length=2000)
    chapter_index: int = Field(default=0, ge=0)
    chapter_title: str | None = Field(default=None, max_length=255)


class OnlineSearchResultPreview(ORMModel):
    source_id: int
    source_name: str
    source_kind: Literal["online"] = "online"
    remote_book_id: str | None = None
    title: str
    author: str | None = None
    description: str | None = None
    cover_url: str | None = None
    detail_url: str


class OnlineDiscoverySearchResponse(ORMModel):
    items: list[OnlineSearchResultPreview]


class OnlinePreviewFields(ORMModel):
    source_id: int
    source_name: str
    detail_url: str
    catalog_url: str
    remote_book_id: str | None = None


class LibraryBookDetailPreview(ORMModel):
    source_kind: Literal["online"] = "online"
    source_label: str
    title: str
    author: str | None = None
    description: str | None = None
    cover_url: str | None = None
    online_fields: OnlinePreviewFields


class OnlineCatalogSourceLocator(ORMModel):
    url: str


class CatalogItemPreview(ORMModel):
    chapter_index: int
    chapter_title: str
    source_locator: OnlineCatalogSourceLocator


class OnlineDiscoveryCatalogResponse(ORMModel):
    items: list[CatalogItemPreview]


class OnlineChapterSourceLocator(ORMModel):
    url: str


class ChapterContentPreview(ORMModel):
    chapter_index: int
    chapter_title: str
    content: str
    content_format: Literal["plain_text"] = "plain_text"
    source_locator: OnlineChapterSourceLocator
