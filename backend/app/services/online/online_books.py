import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.book_group import BookGroup
from app.models.online_catalog_entry import OnlineCatalogEntry
from app.models.online_chapter_cache import OnlineChapterCache
from app.models.online_shelf_book import OnlineShelfBook
from app.schemas.online_book import (
    OnlineBookAddRequest,
    OnlineBookRead,
    OnlineCatalogEntryRead,
    OnlineChapterContentRead,
)
from app.services.book_groups import ensure_default_group, get_user_groups_by_ids
from app.services.online.source_engine import preview_catalog, preview_chapter, preview_detail


class OnlineBookNotFoundError(ValueError):
    pass


def add_online_book_to_shelf(
    db: Session,
    user_id: int,
    payload: OnlineBookAddRequest,
) -> OnlineShelfBook:
    existing_book = _get_existing_online_book(db, user_id, payload.source_id, payload.detail_url)
    if existing_book is not None:
        return existing_book

    detail_preview = preview_detail(
        db,
        user_id,
        payload.source_id,
        detail_url=payload.detail_url,
        remote_book_id=payload.remote_book_id,
    )
    catalog_preview = preview_catalog(
        db,
        user_id,
        payload.source_id,
        catalog_url=detail_preview.online_fields.catalog_url,
    )

    online_book = OnlineShelfBook(
        user_id=user_id,
        source_id=payload.source_id,
        title=detail_preview.title,
        author=detail_preview.author,
        cover_url=detail_preview.cover_url,
        description=detail_preview.description,
        remote_book_id=payload.remote_book_id,
        detail_url=payload.detail_url,
        total_chapters=len(catalog_preview.items),
        latest_catalog_fetched_at=_utcnow(),
    )
    db.add(online_book)
    db.flush()
    default_group = ensure_default_group(db, user_id)
    online_book.groups.append(default_group)

    for chapter in catalog_preview.items:
        db.add(
            OnlineCatalogEntry(
                online_book_id=online_book.id,
                chapter_index=chapter.chapter_index,
                chapter_title=chapter.chapter_title,
                chapter_url=chapter.source_locator.url,
            )
        )

    db.commit()
    return get_user_online_book(db, user_id, online_book.id)


def get_user_online_book(db: Session, user_id: int, online_book_id: int) -> OnlineShelfBook:
    statement = (
        select(OnlineShelfBook)
        .options(joinedload(OnlineShelfBook.source), joinedload(OnlineShelfBook.groups))
        .where(OnlineShelfBook.id == online_book_id, OnlineShelfBook.user_id == user_id)
    )
    online_book = db.execute(statement).unique().scalar_one_or_none()
    if online_book is None:
        raise OnlineBookNotFoundError("Online book not found")
    return online_book


def list_user_online_catalog(db: Session, user_id: int, online_book_id: int) -> list[OnlineCatalogEntry]:
    online_book = get_user_online_book(db, user_id, online_book_id)
    statement = (
        select(OnlineCatalogEntry)
        .where(OnlineCatalogEntry.online_book_id == online_book.id)
        .order_by(OnlineCatalogEntry.chapter_index.asc())
    )
    return list(db.execute(statement).scalars().all())


def list_user_online_book_groups(db: Session, user_id: int, online_book_id: int) -> list[BookGroup]:
    online_book = get_user_online_book(db, user_id, online_book_id)
    return list(online_book.groups)


def update_user_online_book_groups(db: Session, user_id: int, online_book_id: int, group_ids: list[int]) -> list[BookGroup]:
    online_book = get_user_online_book(db, user_id, online_book_id)
    groups = get_user_groups_by_ids(db, user_id, group_ids)
    online_book.groups = groups
    db.commit()
    db.refresh(online_book)
    return list(online_book.groups)


def get_user_online_chapter(
    db: Session,
    user_id: int,
    online_book_id: int,
    chapter_index: int,
) -> OnlineChapterContentRead:
    online_book = get_user_online_book(db, user_id, online_book_id)
    chapter_entry = _get_catalog_entry(db, online_book.id, chapter_index)
    chapter_cache = _get_chapter_cache(db, online_book.id, chapter_index)
    if chapter_cache is not None:
        return serialize_online_chapter_content(chapter_cache, chapter_entry.chapter_title)

    chapter_preview = preview_chapter(
        db,
        user_id,
        online_book.source_id,
        chapter_url=chapter_entry.chapter_url,
        chapter_index=chapter_entry.chapter_index,
        chapter_title=chapter_entry.chapter_title,
    )
    chapter_cache = OnlineChapterCache(
        online_book_id=online_book.id,
        chapter_index=chapter_entry.chapter_index,
        content_text=chapter_preview.content,
        content_length=len(chapter_preview.content),
        source_url=chapter_preview.source_locator.url,
        content_hash=hashlib.sha256(chapter_preview.content.encode("utf-8")).hexdigest(),
    )
    db.add(chapter_cache)
    db.commit()
    db.refresh(chapter_cache)
    return serialize_online_chapter_content(chapter_cache, chapter_entry.chapter_title)


def delete_user_online_book(db: Session, user_id: int, online_book_id: int) -> None:
    online_book = get_user_online_book(db, user_id, online_book_id)
    db.delete(online_book)
    db.commit()


def serialize_online_book(online_book: OnlineShelfBook) -> OnlineBookRead:
    return OnlineBookRead.model_validate(
        {
            "id": online_book.id,
            "user_id": online_book.user_id,
            "source_id": online_book.source_id,
            "source_name": online_book.source.name,
            "title": online_book.title,
            "author": online_book.author,
            "cover_url": online_book.cover_url,
            "description": online_book.description,
            "remote_book_id": online_book.remote_book_id,
            "detail_url": online_book.detail_url,
            "total_chapters": online_book.total_chapters,
            "latest_catalog_fetched_at": online_book.latest_catalog_fetched_at,
            "created_at": online_book.created_at,
            "updated_at": online_book.updated_at,
            "groups": [{"id": group.id, "name": group.name} for group in online_book.groups],
        }
    )


def serialize_online_catalog_entry(entry: OnlineCatalogEntry) -> OnlineCatalogEntryRead:
    return OnlineCatalogEntryRead.model_validate(
        {
            "id": entry.id,
            "online_book_id": entry.online_book_id,
            "chapter_index": entry.chapter_index,
            "chapter_title": entry.chapter_title,
            "chapter_url": entry.chapter_url,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
    )


def serialize_online_chapter_content(cache_entry: OnlineChapterCache, chapter_title: str) -> OnlineChapterContentRead:
    return OnlineChapterContentRead.model_validate(
        {
            "online_book_id": cache_entry.online_book_id,
            "chapter_index": cache_entry.chapter_index,
            "chapter_title": chapter_title,
            "content": cache_entry.content_text,
            "content_length": cache_entry.content_length,
            "source_url": cache_entry.source_url,
        }
    )


def _get_existing_online_book(db: Session, user_id: int, source_id: int, detail_url: str) -> OnlineShelfBook | None:
    statement = (
        select(OnlineShelfBook)
        .options(joinedload(OnlineShelfBook.source), joinedload(OnlineShelfBook.groups))
        .where(
            OnlineShelfBook.user_id == user_id,
            OnlineShelfBook.source_id == source_id,
            OnlineShelfBook.detail_url == detail_url,
        )
    )
    return db.execute(statement).unique().scalar_one_or_none()


def _get_catalog_entry(db: Session, online_book_id: int, chapter_index: int) -> OnlineCatalogEntry:
    statement = select(OnlineCatalogEntry).where(
        OnlineCatalogEntry.online_book_id == online_book_id,
        OnlineCatalogEntry.chapter_index == chapter_index,
    )
    chapter_entry = db.execute(statement).scalar_one_or_none()
    if chapter_entry is None:
        raise OnlineBookNotFoundError("Online chapter not found")
    return chapter_entry


def _get_chapter_cache(db: Session, online_book_id: int, chapter_index: int) -> OnlineChapterCache | None:
    statement = select(OnlineChapterCache).where(
        OnlineChapterCache.online_book_id == online_book_id,
        OnlineChapterCache.chapter_index == chapter_index,
    )
    return db.execute(statement).scalar_one_or_none()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
