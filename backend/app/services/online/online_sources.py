import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.online_source import OnlineSource
from app.schemas.online_source import (
    OnlineSourceCreate,
    OnlineSourceRead,
    OnlineSourceUpdate,
    OnlineSourceValidateRequest,
    OnlineSourceValidateResponse,
)
from app.services.online.source_normalizer import normalize_online_source_payload
from app.services.online.source_validator import validate_phase1_source_definition


class OnlineSourceError(ValueError):
    pass


class OnlineSourceNotFoundError(OnlineSourceError):
    pass


def list_online_sources(db: Session, user_id: int) -> list[OnlineSource]:
    statement = (
        select(OnlineSource)
        .where(OnlineSource.user_id == user_id)
        .order_by(OnlineSource.created_at.desc(), OnlineSource.id.desc())
    )
    return list(db.execute(statement).scalars().all())


def get_online_source(db: Session, user_id: int, source_id: int) -> OnlineSource:
    statement = select(OnlineSource).where(OnlineSource.user_id == user_id, OnlineSource.id == source_id)
    source = db.execute(statement).scalar_one_or_none()
    if source is None:
        raise OnlineSourceNotFoundError("Online source not found")
    return source


def create_online_source(db: Session, user_id: int, payload: OnlineSourceCreate) -> OnlineSource:
    normalized_base_url, normalized_definition = _validate_and_normalize(payload.base_url, payload.definition)
    source = OnlineSource(
        user_id=user_id,
        name=payload.name.strip(),
        description=_normalize_optional_text(payload.description),
        enabled=payload.enabled,
        base_url=normalized_base_url,
        definition_json=json.dumps(normalized_definition, ensure_ascii=False, separators=(",", ":")),
        validation_status="valid",
        validation_errors_json="[]",
        last_checked_at=_utcnow(),
    )
    db.add(source)
    _commit_or_raise(db)
    db.refresh(source)
    return source


def update_online_source(db: Session, user_id: int, source_id: int, payload: OnlineSourceUpdate) -> OnlineSource:
    source = get_online_source(db, user_id, source_id)
    normalized_base_url, normalized_definition = _validate_and_normalize(payload.base_url, payload.definition)
    source.name = payload.name.strip()
    source.description = _normalize_optional_text(payload.description)
    source.enabled = payload.enabled
    source.base_url = normalized_base_url
    source.definition_json = json.dumps(normalized_definition, ensure_ascii=False, separators=(",", ":"))
    source.validation_status = "valid"
    source.validation_errors_json = "[]"
    source.last_checked_at = _utcnow()
    _commit_or_raise(db)
    db.refresh(source)
    return source


def delete_online_source(db: Session, user_id: int, source_id: int) -> None:
    source = get_online_source(db, user_id, source_id)
    db.delete(source)
    db.commit()


def validate_online_source_payload(payload: OnlineSourceValidateRequest) -> OnlineSourceValidateResponse:
    normalized_base_url, normalized_definition = _validate_and_normalize(payload.base_url, payload.definition)
    return OnlineSourceValidateResponse.model_validate(
        {
            "is_valid": True,
            "normalized_base_url": normalized_base_url,
            "normalized_definition": normalized_definition,
            "errors": [],
            "warnings": [],
        }
    )


def serialize_online_source(source: OnlineSource) -> OnlineSourceRead:
    return OnlineSourceRead.model_validate(
        {
            "id": source.id,
            "user_id": source.user_id,
            "name": source.name,
            "description": source.description,
            "enabled": source.enabled,
            "base_url": source.base_url,
            "definition": json.loads(source.definition_json),
            "validation_status": source.validation_status,
            "validation_errors": json.loads(source.validation_errors_json or "[]"),
            "last_checked_at": source.last_checked_at,
            "created_at": source.created_at,
            "updated_at": source.updated_at,
        }
    )


def _validate_and_normalize(base_url: str, definition: Any) -> tuple[str, dict[str, Any]]:
    normalized_base_url, normalized_definition = normalize_online_source_payload(
        OnlineSourceValidateRequest(base_url=base_url, definition=definition)
    )
    validate_phase1_source_definition(normalized_base_url, normalized_definition)
    return normalized_base_url, normalized_definition


def _commit_or_raise(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise OnlineSourceError("Online source name already exists") from exc


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
