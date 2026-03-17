from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.online_source import (
    OnlineSourceCreate,
    OnlineSourceRead,
    OnlineSourceUpdate,
    OnlineSourceValidateRequest,
    OnlineSourceValidateResponse,
)
from app.services.online.online_sources import (
    OnlineSourceError,
    OnlineSourceNotFoundError,
    create_online_source,
    delete_online_source,
    get_online_source,
    list_online_sources,
    serialize_online_source,
    update_online_source,
    validate_online_source_payload,
)
from app.services.online.source_validator import OnlineSourceValidationError


router = APIRouter(prefix="/api/online-sources", tags=["online-sources"])


@router.post("/validate", response_model=OnlineSourceValidateResponse)
def validate_online_source(
    payload: OnlineSourceValidateRequest,
    current_user: CurrentUser,
) -> OnlineSourceValidateResponse:
    _ = current_user
    try:
        return validate_online_source_payload(payload)
    except OnlineSourceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("", response_model=OnlineSourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: OnlineSourceCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineSourceRead:
    try:
        source = create_online_source(db, current_user.id, payload)
    except (OnlineSourceError, OnlineSourceValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_online_source(source)


@router.get("", response_model=list[OnlineSourceRead])
def get_sources(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[OnlineSourceRead]:
    return [serialize_online_source(source) for source in list_online_sources(db, current_user.id)]


@router.get("/{source_id}", response_model=OnlineSourceRead)
def get_source(source_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> OnlineSourceRead:
    try:
        source = get_online_source(db, current_user.id, source_id)
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return serialize_online_source(source)


@router.put("/{source_id}", response_model=OnlineSourceRead)
def put_source(
    source_id: int,
    payload: OnlineSourceUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> OnlineSourceRead:
    try:
        source = update_online_source(db, current_user.id, source_id, payload)
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (OnlineSourceError, OnlineSourceValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_online_source(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_source(source_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    try:
        delete_online_source(db, current_user.id, source_id)
    except OnlineSourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
