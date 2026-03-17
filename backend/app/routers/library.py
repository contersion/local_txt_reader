from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.library import LibraryBookSummary
from app.services.library import list_library_books


router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/books", response_model=list[LibraryBookSummary])
def get_library_books(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    source_kind: str | None = Query(default=None),
) -> list[LibraryBookSummary]:
    return list_library_books(
        db,
        current_user.id,
        q=q,
        sort_by=sort_by,
        sort_order=sort_order,
        source_kind=source_kind,
    )
