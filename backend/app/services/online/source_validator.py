import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


class OnlineSourceValidationError(ValueError):
    pass


ALLOWED_PLACEHOLDERS = {
    "keyword",
    "page",
    "detail_url",
    "catalog_url",
    "chapter_url",
}
FORBIDDEN_HEADER_NAMES = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "set-cookie",
}
FORBIDDEN_KEYWORDS = (
    "<script",
    "</script",
    "javascript:",
    "eval(",
    "new function",
    "function(",
    "=>",
    "document.cookie",
    "webview",
    "selenium",
    "playwright",
    "anti_bot",
    "antibot",
    "captcha",
)
FORBIDDEN_KEYS = {
    "js",
    "script",
    "scripts",
    "cookie",
    "cookies",
    "authorization",
    "login",
    "session",
    "webview",
    "requests",
    "steps",
    "pipeline",
    "variables",
    "conditions",
}
PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
URL_LIKE_KEYS = {"base_url", "url", "detail_url", "catalog_url", "chapter_url", "cover_url"}
REQUIRED_FIELDS_BY_STAGE = {
    "search": {"title", "detail_url"},
    "detail": {"title", "catalog_url"},
    "catalog": {"chapter_title", "chapter_url"},
    "content": {"content"},
}


@dataclass(frozen=True)
class ValidationResult:
    warnings: list[str]


def validate_phase1_source_definition(base_url: str, definition: dict[str, Any]) -> ValidationResult:
    _validate_base_url(base_url)
    _validate_definition_structure(definition)
    _validate_recursive(definition)
    _validate_stage_contracts(definition)
    return ValidationResult(warnings=[])


def _validate_base_url(base_url: str) -> None:
    parsed_url = urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise OnlineSourceValidationError("base_url must be a valid http/https URL")


def _validate_definition_structure(definition: dict[str, Any]) -> None:
    expected_stages = {"search", "detail", "catalog", "content"}
    missing_stages = [stage for stage in expected_stages if stage not in definition]
    if missing_stages:
        raise OnlineSourceValidationError(f"Missing required stages: {', '.join(sorted(missing_stages))}")


def _validate_recursive(value: Any, *, path: str = "definition") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in FORBIDDEN_KEYS:
                raise OnlineSourceValidationError(f"{path}.{key} uses unsupported capability: {key}")
            _validate_recursive(item, path=f"{path}.{key}")
        return

    if isinstance(value, list):
        raise OnlineSourceValidationError(f"{path} contains unsupported list chaining")

    if isinstance(value, str):
        _validate_string_value(path, value)


def _validate_string_value(path: str, value: str) -> None:
    normalized_value = value.strip()
    lower_value = normalized_value.lower()
    for forbidden_keyword in FORBIDDEN_KEYWORDS:
        if forbidden_keyword in lower_value:
            raise OnlineSourceValidationError(f"{path} contains unsupported capability: {forbidden_keyword}")

    placeholders = PLACEHOLDER_PATTERN.findall(normalized_value)
    for placeholder in placeholders:
        if placeholder not in ALLOWED_PLACEHOLDERS:
            raise OnlineSourceValidationError(f"{path} uses unsupported placeholder: {placeholder}")

    if any(part in path.lower() for part in (".headers.", ".query.", ".body.", ".expr", ".attr", ".join")):
        return

    if path.split(".")[-1].lower() in URL_LIKE_KEYS:
        _validate_url_like_value(path, normalized_value)


def _validate_url_like_value(path: str, value: str) -> None:
    if not value:
        raise OnlineSourceValidationError(f"{path} cannot be empty")

    parsed_url = urlparse(value)
    if parsed_url.scheme:
        if parsed_url.scheme not in {"http", "https"}:
            raise OnlineSourceValidationError(f"{path} must use http/https")
        return

    if value.startswith("/") or value.startswith("?") or value.startswith("{{"):
        return

    raise OnlineSourceValidationError(f"{path} must be an absolute http/https URL, relative path, or allowed placeholder")


def _validate_stage_contracts(definition: dict[str, Any]) -> None:
    for stage_name, required_fields in REQUIRED_FIELDS_BY_STAGE.items():
        stage_definition = definition[stage_name]
        request_definition = stage_definition["request"]
        header_names = {name.lower() for name in request_definition.get("headers", {})}
        forbidden_headers = sorted(header_names & FORBIDDEN_HEADER_NAMES)
        if forbidden_headers:
            raise OnlineSourceValidationError(
                f"{stage_name}.request.headers contains unsupported header(s): {', '.join(forbidden_headers)}"
            )

        if stage_name in {"search", "catalog"} and not stage_definition.get("list_selector"):
            raise OnlineSourceValidationError(f"{stage_name} stage requires list_selector")

        stage_fields = set(stage_definition.get("fields", {}))
        missing_fields = sorted(required_fields - stage_fields)
        if missing_fields:
            raise OnlineSourceValidationError(f"{stage_name} stage is missing required field(s): {', '.join(missing_fields)}")
