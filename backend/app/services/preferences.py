import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.preferences import UserPreferencesPatchRequest


DEFAULT_USER_PREFERENCES = {
    "version": 1,
    "bookshelf": {
        "sort": "created_at",
        "search": "",
        "group_id": None,
        "page": 1,
        "page_size": None,
    },
    "reader": {
        "font_size": 19,
        "line_height": 1.95,
        "letter_spacing": 0.0,
        "paragraph_spacing": 1.0,
        "content_width": 72,
        "theme": "light",
    },
}

ALLOWED_BOOK_SORTS = {"created_at", "recent_read", "title"}
ALLOWED_READER_THEMES = {"light", "dark"}


def get_user_preferences(user: User) -> tuple[dict[str, Any], bool]:
    raw_value = user.preferences_json
    has_saved_preferences = isinstance(raw_value, str) and raw_value.strip() != ""
    if not has_saved_preferences:
        return _clone_default_preferences(), False

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return _clone_default_preferences(), True

    return _normalize_user_preferences(payload), True


def update_user_preferences(
    db: Session,
    user: User,
    payload: UserPreferencesPatchRequest,
) -> tuple[dict[str, Any], bool]:
    current_preferences, _ = get_user_preferences(user)
    merged_preferences = _deep_merge(
        current_preferences,
        payload.model_dump(exclude_unset=True),
    )
    normalized_preferences = _normalize_user_preferences(merged_preferences)
    user.preferences_json = json.dumps(
        normalized_preferences,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    db.commit()
    db.refresh(user)
    return normalized_preferences, True


def _normalize_user_preferences(payload: Any) -> dict[str, Any]:
    normalized = _clone_default_preferences()
    raw_payload = payload if isinstance(payload, Mapping) else {}
    normalized["version"] = DEFAULT_USER_PREFERENCES["version"]
    normalized["bookshelf"] = _normalize_bookshelf_preferences(raw_payload.get("bookshelf"))
    normalized["reader"] = _normalize_reader_preferences(raw_payload.get("reader"))
    return normalized


def _normalize_bookshelf_preferences(payload: Any) -> dict[str, Any]:
    normalized = dict(DEFAULT_USER_PREFERENCES["bookshelf"])
    raw_payload = payload if isinstance(payload, Mapping) else {}

    sort = raw_payload.get("sort")
    if sort in ALLOWED_BOOK_SORTS:
        normalized["sort"] = sort

    search = raw_payload.get("search")
    if isinstance(search, str):
        normalized["search"] = search.strip()[:200]

    normalized["group_id"] = _normalize_optional_positive_int(raw_payload.get("group_id"))
    normalized["page"] = _normalize_positive_int(raw_payload.get("page"), fallback=1)
    normalized["page_size"] = _normalize_optional_positive_int(raw_payload.get("page_size"), maximum=100)
    return normalized


def _normalize_reader_preferences(payload: Any) -> dict[str, Any]:
    normalized = dict(DEFAULT_USER_PREFERENCES["reader"])
    raw_payload = payload if isinstance(payload, Mapping) else {}

    normalized["font_size"] = int(_clamp_number(raw_payload.get("font_size"), 15, 32, normalized["font_size"]))
    normalized["line_height"] = round(_clamp_number(raw_payload.get("line_height"), 1.45, 2.6, normalized["line_height"]), 2)
    normalized["letter_spacing"] = round(_clamp_number(raw_payload.get("letter_spacing"), 0.0, 2.0, normalized["letter_spacing"]), 2)
    normalized["paragraph_spacing"] = round(
        _clamp_number(raw_payload.get("paragraph_spacing"), 0.0, 2.5, normalized["paragraph_spacing"]),
        2,
    )
    normalized["content_width"] = int(_clamp_number(raw_payload.get("content_width"), 56, 96, normalized["content_width"]))

    theme = raw_payload.get("theme")
    if theme in ALLOWED_READER_THEMES:
        normalized["theme"] = theme

    return normalized


def _clone_default_preferences() -> dict[str, Any]:
    return {
        "version": DEFAULT_USER_PREFERENCES["version"],
        "bookshelf": dict(DEFAULT_USER_PREFERENCES["bookshelf"]),
        "reader": dict(DEFAULT_USER_PREFERENCES["reader"]),
    }


def _deep_merge(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in patch.items():
        current_value = merged.get(key)
        if isinstance(current_value, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(current_value, value)
            continue
        merged[key] = value
    return merged


def _normalize_positive_int(value: Any, *, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return value if value >= 1 else fallback
    if isinstance(value, float) and value.is_integer():
        return int(value) if value >= 1 else fallback
    return fallback


def _normalize_optional_positive_int(value: Any, *, maximum: int | None = None) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    normalized: int | None
    if isinstance(value, int):
        normalized = value if value >= 1 else None
    elif isinstance(value, float) and value.is_integer():
        normalized = int(value) if value >= 1 else None
    else:
        normalized = None

    if normalized is None:
        return None
    if maximum is not None and normalized > maximum:
        return None
    return normalized


def _clamp_number(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return fallback
    normalized = float(value)
    if normalized < minimum:
        return fallback
    if normalized > maximum:
        return fallback
    return normalized
