from typing import Any
from urllib.parse import urlparse

from app.schemas.online_source import OnlineSourceBase, OnlineSourceDefinition, OnlineSourceValidateRequest


def normalize_online_source_payload(
    payload: OnlineSourceBase | OnlineSourceValidateRequest,
) -> tuple[str, dict[str, Any]]:
    normalized_base_url = normalize_base_url(payload.base_url)
    normalized_definition = normalize_source_definition(payload.definition)
    return normalized_base_url, normalized_definition


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    parsed_url = urlparse(normalized)
    if parsed_url.scheme and parsed_url.netloc and parsed_url.path == "":
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    return normalized


def normalize_source_definition(definition: OnlineSourceDefinition | dict[str, Any]) -> dict[str, Any]:
    raw_definition = definition.model_dump(exclude_none=True) if isinstance(definition, OnlineSourceDefinition) else definition
    normalized_definition: dict[str, Any] = {}

    for stage_name, stage_definition in raw_definition.items():
        normalized_definition[stage_name] = {
            "request": _normalize_request(stage_definition["request"]),
            "fields": _normalize_fields(stage_definition.get("fields", {})),
        }
        if "list_selector" in stage_definition and stage_definition["list_selector"] is not None:
            normalized_definition[stage_name]["list_selector"] = _normalize_list_selector(stage_definition["list_selector"])

    return normalized_definition


def _normalize_request(request_definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": str(request_definition["method"]).upper(),
        "url": str(request_definition["url"]).strip(),
        "response_type": str(request_definition["response_type"]).lower(),
        "headers": _normalize_string_mapping(request_definition.get("headers", {})),
        "query": _normalize_string_mapping(request_definition.get("query", {})),
        "body": _normalize_string_mapping(request_definition.get("body", {})),
    }


def _normalize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    normalized_fields: dict[str, Any] = {}
    for field_name, field_definition in fields.items():
        normalized_name = str(field_name).strip()
        normalized_fields[normalized_name] = {
            "parser": str(field_definition["parser"]).lower(),
            "expr": str(field_definition["expr"]).strip(),
            "trim": bool(field_definition.get("trim", True)),
            "required": bool(field_definition.get("required", False)),
        }
        if field_definition.get("attr") is not None:
            normalized_fields[normalized_name]["attr"] = str(field_definition["attr"]).strip()
        if field_definition.get("regex_group") is not None:
            normalized_fields[normalized_name]["regex_group"] = int(field_definition["regex_group"])
        if field_definition.get("join") is not None:
            normalized_fields[normalized_name]["join"] = str(field_definition["join"])
    return normalized_fields


def _normalize_list_selector(list_selector: dict[str, Any]) -> dict[str, Any]:
    return {
        "parser": str(list_selector["parser"]).lower(),
        "expr": str(list_selector["expr"]).strip(),
    }


def _normalize_string_mapping(value: dict[str, Any]) -> dict[str, str]:
    return {
        str(key).strip(): str(item).strip()
        for key, item in value.items()
        if str(key).strip()
    }
