from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.models.online_reading_progress import OnlineReadingProgress
from app.models.online_shelf_book import OnlineShelfBook
from app.schemas.library import LibraryBookSourceMeta, LibraryBookSummary
from app.services.books import list_user_books


LibrarySortBy = Literal["created_at", "recent_read_at", "title"]
LibrarySortOrder = Literal["asc", "desc"]
LibrarySourceKind = Literal["local", "online"]

DEFAULT_SORT_BY: LibrarySortBy = "created_at"
DEFAULT_SORT_ORDER: LibrarySortOrder = "desc"


def list_library_books(
    db: Session,
    user_id: int,
    *,
    q: str | None = None,
    sort_by: str = DEFAULT_SORT_BY,
    sort_order: str = DEFAULT_SORT_ORDER,
    source_kind: str | None = None,
) -> list[LibraryBookSummary]:
    normalized_sort_by = _normalize_sort_by(sort_by)
    normalized_sort_order = _normalize_sort_order(sort_order)
    normalized_source_kind = _normalize_source_kind(source_kind)
    search_query = (q or "").strip().casefold()

    summaries: list[LibraryBookSummary] = []
    if normalized_source_kind in (None, "local"):
        summaries.extend(_list_local_library_books(db, user_id))
    if normalized_source_kind in (None, "online"):
        summaries.extend(_list_online_library_books(db, user_id))

    if search_query:
        summaries = [item for item in summaries if _matches_search(item, search_query)]

    return _sort_library_books(summaries, normalized_sort_by, normalized_sort_order)


def _list_local_library_books(db: Session, user_id: int) -> list[LibraryBookSummary]:
    local_books = list_user_books(db, user_id)
    return [
        LibraryBookSummary.model_validate(
            {
                "library_id": f"local:{book['id']}",
                "source_kind": "local",
                "source_label": "本地TXT",
                "entity_id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "cover_url": book["cover_url"],
                "total_chapters": book["total_chapters"],
                "total_words": book["total_words"],
                "progress_percent": book["progress_percent"],
                "recent_read_at": book["recent_read_at"],
                "created_at": book["created_at"],
                "updated_at": book["updated_at"],
                "groups": book["groups"],
                "source_meta": None,
            }
        )
        for book in local_books
    ]


def _list_online_library_books(db: Session, user_id: int) -> list[LibraryBookSummary]:
    statement = (
        select(OnlineShelfBook, OnlineReadingProgress)
        .options(joinedload(OnlineShelfBook.source), joinedload(OnlineShelfBook.groups))
        .outerjoin(
            OnlineReadingProgress,
            and_(
                OnlineReadingProgress.online_book_id == OnlineShelfBook.id,
                OnlineReadingProgress.user_id == user_id,
            ),
        )
        .where(OnlineShelfBook.user_id == user_id)
    )
    rows = db.execute(statement).unique().all()
    return [
        LibraryBookSummary.model_validate(
            {
                "library_id": f"online:{online_book.id}",
                "source_kind": "online",
                "source_label": online_book.source.name,
                "entity_id": online_book.id,
                "title": online_book.title,
                "author": online_book.author,
                "cover_url": online_book.cover_url,
                "total_chapters": online_book.total_chapters,
                "total_words": None,
                "progress_percent": progress.percent if progress is not None else None,
                "recent_read_at": _ensure_utc_datetime(progress.updated_at) if progress is not None else None,
                "created_at": online_book.created_at,
                "updated_at": online_book.updated_at,
                "groups": [{"id": group.id, "name": group.name} for group in online_book.groups],
                "source_meta": LibraryBookSourceMeta.model_validate(
                    {
                        "source_id": online_book.source_id,
                        "remote_book_id": online_book.remote_book_id,
                        "detail_url": online_book.detail_url,
                    }
                ),
            }
        )
        for online_book, progress in rows
    ]


def _matches_search(item: LibraryBookSummary, query: str) -> bool:
    title = item.title.casefold()
    author = (item.author or "").casefold()
    return query in title or query in author


def _sort_library_books(
    items: list[LibraryBookSummary],
    sort_by: LibrarySortBy,
    sort_order: LibrarySortOrder,
) -> list[LibraryBookSummary]:
    reverse = sort_order == "desc"
    if sort_by == "title":
        return sorted(items, key=_title_sort_key, reverse=reverse)
    if sort_by == "recent_read_at":
        return sorted(items, key=lambda item: _datetime_sort_key(item.recent_read_at), reverse=reverse)
    return sorted(items, key=lambda item: _datetime_sort_key(item.created_at), reverse=reverse)


def _title_sort_key(item: LibraryBookSummary):
    title = item.title.strip()
    leading_char = title[:1]
    cjk_first_bucket = 0 if leading_char and not leading_char.isascii() else 1
    return (cjk_first_bucket, title.casefold(), item.entity_id)


def _datetime_sort_key(value: datetime | None):
    normalized = _ensure_utc_datetime(value) if value is not None else datetime.min.replace(tzinfo=timezone.utc)
    return (value is None, normalized)


def _normalize_sort_by(value: str) -> LibrarySortBy:
    return value if value in {"created_at", "recent_read_at", "title"} else DEFAULT_SORT_BY


def _normalize_sort_order(value: str) -> LibrarySortOrder:
    return value if value in {"asc", "desc"} else DEFAULT_SORT_ORDER


def _normalize_source_kind(value: str | None) -> LibrarySourceKind | None:
    if value in {"local", "online"}:
        return value
    return None


def _ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
