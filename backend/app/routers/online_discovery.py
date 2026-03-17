from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.online_discovery import (
    ChapterContentPreview,
    LibraryBookDetailPreview,
    OnlineDiscoveryCatalogRequest,
    OnlineDiscoveryCatalogResponse,
    OnlineDiscoveryChapterRequest,
    OnlineDiscoveryDetailRequest,
    OnlineDiscoverySearchRequest,
    OnlineDiscoverySearchResponse,
)
from app.services.online.online_sources import OnlineSourceNotFoundError
from app.services.online.source_engine import (
    OnlineDiscoveryError,
    preview_catalog,
    preview_chapter,
    preview_detail,
    preview_search,
)


router = APIRouter(prefix="/api/online-discovery", tags=["online-discovery"])


@router.post("/search", response_model=OnlineDiscoverySearchResponse)
def post_online_search_preview(
    payload: OnlineDiscoverySearchRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineDiscoverySearchResponse:
    try:
        return preview_search(db, current_user.id, payload.source_id, keyword=payload.keyword, page=payload.page)
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/detail", response_model=LibraryBookDetailPreview)
def post_online_detail_preview(
    payload: OnlineDiscoveryDetailRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LibraryBookDetailPreview:
    try:
        return preview_detail(
            db,
            current_user.id,
            payload.source_id,
            detail_url=payload.detail_url,
            remote_book_id=payload.remote_book_id,
        )
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/catalog", response_model=OnlineDiscoveryCatalogResponse)
def post_online_catalog_preview(
    payload: OnlineDiscoveryCatalogRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineDiscoveryCatalogResponse:
    try:
        return preview_catalog(db, current_user.id, payload.source_id, catalog_url=payload.catalog_url)
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chapter", response_model=ChapterContentPreview)
def post_online_chapter_preview(
    payload: OnlineDiscoveryChapterRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ChapterContentPreview:
    try:
        return preview_chapter(
            db,
            current_user.id,
            payload.source_id,
            chapter_url=payload.chapter_url,
            chapter_index=payload.chapter_index,
            chapter_title=payload.chapter_title,
        )
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OnlineDiscoveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
