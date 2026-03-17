from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.online_reading_progress import OnlineReadingProgress
from app.schemas.online_book import OnlineReadingProgressSyncRequest
from app.services.online.online_books import OnlineBookNotFoundError, get_user_online_book


class OnlineReadingProgressNotFoundError(ValueError):
    pass


def get_online_reading_progress(db: Session, user_id: int, online_book_id: int) -> OnlineReadingProgress:
    get_user_online_book(db, user_id, online_book_id)
    progress = _get_progress_row(db, user_id, online_book_id)
    if progress is None:
        raise OnlineReadingProgressNotFoundError("Online reading progress not found")
    progress.updated_at = _ensure_utc_datetime(progress.updated_at)
    return progress


def upsert_online_reading_progress(
    db: Session,
    user_id: int,
    online_book_id: int,
    payload: OnlineReadingProgressSyncRequest,
) -> OnlineReadingProgress:
    get_user_online_book(db, user_id, online_book_id)
    incoming_updated_at = _ensure_utc_datetime(payload.updated_at)
    progress = _get_progress_row(db, user_id, online_book_id)

    if progress is None:
        progress = OnlineReadingProgress(
            user_id=user_id,
            online_book_id=online_book_id,
            chapter_index=payload.chapter_index,
            char_offset=payload.char_offset,
            percent=payload.percent,
            updated_at=incoming_updated_at,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
        progress.updated_at = _ensure_utc_datetime(progress.updated_at)
        return progress

    current_updated_at = _ensure_utc_datetime(progress.updated_at)
    if current_updated_at > incoming_updated_at:
        progress.updated_at = current_updated_at
        return progress

    progress.chapter_index = payload.chapter_index
    progress.char_offset = payload.char_offset
    progress.percent = payload.percent
    progress.updated_at = incoming_updated_at
    db.commit()
    db.refresh(progress)
    progress.updated_at = _ensure_utc_datetime(progress.updated_at)
    return progress


def _get_progress_row(db: Session, user_id: int, online_book_id: int) -> OnlineReadingProgress | None:
    statement = select(OnlineReadingProgress).where(
        OnlineReadingProgress.user_id == user_id,
        OnlineReadingProgress.online_book_id == online_book_id,
    )
    return db.execute(statement).scalar_one_or_none()


def _ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
