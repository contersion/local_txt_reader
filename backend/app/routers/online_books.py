from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.online_book import (
    OnlineBookAddRequest,
    OnlineBookRead,
    OnlineCatalogEntryRead,
    OnlineChapterContentRead,
    OnlineReadingProgressRead,
    OnlineReadingProgressSyncRequest,
)
from app.schemas.book_group import BookGroupAssignmentUpdate, BookGroupSummary
from app.services.online.online_books import (
    OnlineBookNotFoundError,
    add_online_book_to_shelf,
    delete_user_online_book,
    get_user_online_book,
    get_user_online_chapter,
    list_user_online_book_groups,
    list_user_online_catalog,
    serialize_online_book,
    serialize_online_catalog_entry,
    update_user_online_book_groups,
)
from app.services.book_groups import BookGroupError
from app.services.online.online_progress import (
    OnlineReadingProgressNotFoundError,
    get_online_reading_progress,
    upsert_online_reading_progress,
)
from app.services.online.source_engine import OnlineDiscoveryError


router = APIRouter(prefix="/api/online-books", tags=["online-books"])


@router.post("", response_model=OnlineBookRead)
def post_online_book(
    payload: OnlineBookAddRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineBookRead:
    try:
        online_book = add_online_book_to_shelf(db, current_user.id, payload)
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_online_book(online_book)


@router.get("/{online_book_id}", response_model=OnlineBookRead)
def get_online_book(
    online_book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineBookRead:
    try:
        online_book = get_user_online_book(db, current_user.id, online_book_id)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return serialize_online_book(online_book)


@router.get("/{online_book_id}/catalog", response_model=list[OnlineCatalogEntryRead])
def get_online_book_catalog(
    online_book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[OnlineCatalogEntryRead]:
    try:
        entries = list_user_online_catalog(db, current_user.id, online_book_id)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [serialize_online_catalog_entry(entry) for entry in entries]


@router.get("/{online_book_id}/groups", response_model=list[BookGroupSummary])
def get_online_book_groups(
    online_book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[BookGroupSummary]:
    try:
        groups = list_user_online_book_groups(db, current_user.id, online_book_id)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [BookGroupSummary.model_validate(group) for group in groups]


@router.put("/{online_book_id}/groups", response_model=list[BookGroupSummary])
def put_online_book_groups(
    online_book_id: int,
    payload: BookGroupAssignmentUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[BookGroupSummary]:
    try:
        groups = update_user_online_book_groups(db, current_user.id, online_book_id, payload.group_ids)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookGroupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [BookGroupSummary.model_validate(group) for group in groups]


@router.get("/{online_book_id}/chapters/{chapter_index}", response_model=OnlineChapterContentRead)
def get_online_book_chapter(
    online_book_id: int,
    chapter_index: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineChapterContentRead:
    try:
        return get_user_online_chapter(db, current_user.id, online_book_id, chapter_index)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{online_book_id}/progress", response_model=OnlineReadingProgressRead)
def get_online_book_progress(
    online_book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineReadingProgressRead:
    try:
        progress = get_online_reading_progress(db, current_user.id, online_book_id)
    except (OnlineBookNotFoundError, OnlineReadingProgressNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OnlineReadingProgressRead.model_validate(progress)


@router.put("/{online_book_id}/progress", response_model=OnlineReadingProgressRead)
def put_online_book_progress(
    online_book_id: int,
    payload: OnlineReadingProgressSyncRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineReadingProgressRead:
    try:
        progress = upsert_online_reading_progress(db, current_user.id, online_book_id, payload)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OnlineReadingProgressRead.model_validate(progress)


@router.delete("/{online_book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_online_book(
    online_book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_user_online_book(db, current_user.id, online_book_id)
    except OnlineBookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
