from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from app.schemas.online_runtime import (
    HeaderTemplateSpec,
    LegadoRuntimeCode,
    OnlineAuthConfig,
    OnlineAuthMode,
    RequestBodyMode,
    RequestProfile,
    RequestRuntimeDescriptor,
    SessionCookie,
    SessionContext,
    SignaturePlaceholderSpec,
)


class RequestProfileError(ValueError):
    def __init__(self, code: LegadoRuntimeCode, message: str):
        super().__init__(message)
        self.code = code


def build_request_profile(
    *,
    stage_request: Mapping[str, Any],
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
    runtime_descriptor: RequestRuntimeDescriptor | Mapping[str, Any] | None = None,
) -> RequestProfile:
    normalized_auth_config = auth_config or OnlineAuthConfig()
    _validate_auth_config(normalized_auth_config)
    _validate_session_requirements(normalized_auth_config, session_context)
    normalized_runtime_descriptor = _resolve_runtime_descriptor(stage_request, runtime_descriptor)
    _validate_request_runtime_descriptor(normalized_runtime_descriptor, stage_request)

    headers = _normalize_mapping(dict(stage_request.get("headers") or {}))
    if session_context is not None:
        for header_name, header_value in _normalize_mapping(session_context.headers).items():
            headers.setdefault(header_name, header_value)

    return RequestProfile.model_validate(
        {
            "method": str(stage_request["method"]).upper(),
            "url": str(stage_request["url"]).strip(),
            "response_type": str(stage_request["response_type"]).lower(),
            "headers": headers,
            "query": _normalize_mapping(dict(stage_request.get("query") or {})),
            "body": _normalize_mapping(dict(stage_request.get("body") or {})),
            "cookies": _collect_active_cookies(session_context.cookies if session_context is not None else ()),
        }
    )


def _validate_auth_config(auth_config: OnlineAuthConfig) -> None:
    if auth_config.login_required and auth_config.mode == OnlineAuthMode.NONE:
        raise RequestProfileError(
            LegadoRuntimeCode.AUTH_CONFIG_INVALID,
            "login_required cannot be enabled when auth mode is 'none'",
        )

    if auth_config.mode in {OnlineAuthMode.TOKEN, OnlineAuthMode.HEADER} and not auth_config.token_header_name:
        raise RequestProfileError(
            LegadoRuntimeCode.AUTH_CONFIG_INVALID,
            "token_header_name is required for token/header auth modes",
        )


def _validate_session_requirements(
    auth_config: OnlineAuthConfig,
    session_context: SessionContext | None,
) -> None:
    if auth_config.login_required and session_context is None:
        raise RequestProfileError(
            LegadoRuntimeCode.SESSION_MISSING,
            "Authenticated session is required but missing",
        )

    if session_context is not None and _is_expired(session_context.expires_at):
        raise RequestProfileError(
            LegadoRuntimeCode.SESSION_EXPIRED,
            "Authenticated session has expired",
        )


def _collect_active_cookies(cookies: list[SessionCookie] | tuple[SessionCookie, ...]) -> dict[str, str]:
    active_cookies: dict[str, str] = {}
    for cookie in cookies:
        if _is_expired(cookie.expires_at):
            continue
        active_cookies[cookie.name] = cookie.value
    return active_cookies


def _normalize_mapping(values: Mapping[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in values.items():
        normalized_key = str(key).strip()
        normalized_value = str(value).strip()
        if not normalized_key or not normalized_value:
            continue
        normalized[normalized_key] = normalized_value
    return normalized


def _is_expired(value: datetime | None) -> bool:
    if value is None:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc) <= datetime.now(timezone.utc)


def _resolve_runtime_descriptor(
    stage_request: Mapping[str, Any],
    runtime_descriptor: RequestRuntimeDescriptor | Mapping[str, Any] | None,
) -> RequestRuntimeDescriptor | None:
    raw_descriptor = runtime_descriptor if runtime_descriptor is not None else stage_request.get("runtime")
    if raw_descriptor in (None, {}):
        return None
    if isinstance(raw_descriptor, RequestRuntimeDescriptor):
        return raw_descriptor
    if not isinstance(raw_descriptor, Mapping):
        raise RequestProfileError(
            LegadoRuntimeCode.INVALID_HEADER_TEMPLATE,
            "Runtime descriptor must be a mapping when provided",
        )
    return RequestRuntimeDescriptor.model_validate(dict(raw_descriptor))


def _validate_request_runtime_descriptor(
    descriptor: RequestRuntimeDescriptor | None,
    stage_request: Mapping[str, Any],
) -> None:
    body_mode = _resolve_body_mode(descriptor.body_mode if descriptor is not None else None, stage_request)
    _validate_body_mode(body_mode, stage_request)
    _validate_header_template(descriptor.header_template if descriptor is not None else None)
    _validate_signature_placeholders(descriptor.signature_placeholders if descriptor is not None else None)


def _resolve_body_mode(raw_mode: str | RequestBodyMode | None, stage_request: Mapping[str, Any]) -> RequestBodyMode:
    if raw_mode in (None, ""):
        if _normalize_mapping(dict(stage_request.get("body") or {})):
            return RequestBodyMode.FORM
        return RequestBodyMode.QUERY

    normalized_mode = raw_mode.value if isinstance(raw_mode, RequestBodyMode) else str(raw_mode).strip().lower()
    try:
        return RequestBodyMode(normalized_mode)
    except ValueError as exc:
        raise RequestProfileError(
            LegadoRuntimeCode.UNSUPPORTED_REQUEST_BODY_MODE,
            f"Unsupported request body mode: {normalized_mode or '<empty>'}",
        ) from exc


def _validate_body_mode(body_mode: RequestBodyMode, stage_request: Mapping[str, Any]) -> None:
    if body_mode in {RequestBodyMode.JSON, RequestBodyMode.RAW}:
        raise RequestProfileError(
            LegadoRuntimeCode.UNSUPPORTED_REQUEST_BODY_MODE,
            f"Request body mode '{body_mode.value}' is not implemented in Phase 3-B.2",
        )

    if body_mode == RequestBodyMode.QUERY and _normalize_mapping(dict(stage_request.get("body") or {})):
        raise RequestProfileError(
            LegadoRuntimeCode.UNSUPPORTED_REQUEST_BODY_MODE,
            "Request body mode 'query' cannot be used when a request body is present",
        )


def _validate_header_template(header_template: HeaderTemplateSpec | None) -> None:
    if header_template is None:
        return

    for raw_name, raw_value in header_template.headers.items():
        normalized_name = str(raw_name).strip()
        if not normalized_name:
            raise RequestProfileError(
                LegadoRuntimeCode.INVALID_HEADER_TEMPLATE,
                "Header template contains a blank header name",
            )

        lowered_name = normalized_name.lower()
        if _looks_like_signature_header(lowered_name):
            raise RequestProfileError(
                LegadoRuntimeCode.UNSUPPORTED_SIGNATURE_FLOW,
                f"Header template uses signature-like header '{normalized_name}'",
            )

        if lowered_name in {"authorization", "cookie", "proxy-authorization", "set-cookie"} or lowered_name.startswith("sec-ch-"):
            raise RequestProfileError(
                LegadoRuntimeCode.INVALID_HEADER_TEMPLATE,
                f"Header template uses unsupported header '{normalized_name}'",
            )

        normalized_value = "" if raw_value is None else str(raw_value).strip()
        if not normalized_value:
            continue

        lowered_value = normalized_value.lower()
        if any(marker in lowered_value for marker in ("@js:", "<js", "javascript:", "eval(", "function(", "=>")):
            raise RequestProfileError(
                LegadoRuntimeCode.INVALID_HEADER_TEMPLATE,
                f"Header template for '{normalized_name}' contains an execution marker",
            )

        if "{{" in normalized_value or "}}" in normalized_value or "${" in normalized_value:
            if _looks_like_signature_marker(lowered_value):
                raise RequestProfileError(
                    LegadoRuntimeCode.UNSUPPORTED_SIGNATURE_FLOW,
                    f"Header template for '{normalized_name}' requires unsupported signature placeholders",
                )
            raise RequestProfileError(
                LegadoRuntimeCode.INVALID_HEADER_TEMPLATE,
                f"Header template for '{normalized_name}' contains unsupported dynamic placeholders",
            )


def _validate_signature_placeholders(signature_placeholders: SignaturePlaceholderSpec | None) -> None:
    if signature_placeholders is None:
        return

    normalized_tokens = [str(token).strip() for token in signature_placeholders.tokens if str(token).strip()]
    if not normalized_tokens:
        return

    raise RequestProfileError(
        LegadoRuntimeCode.UNSUPPORTED_SIGNATURE_FLOW,
        "Signature placeholders are modeled for preflight only and are not executable in Phase 3-B.2",
    )


def _looks_like_signature_header(header_name: str) -> bool:
    return (
        header_name.startswith("x-sign")
        or header_name.startswith("x-signature")
        or header_name.startswith("x-timestamp")
        or header_name.startswith("x-nonce")
    )


def _looks_like_signature_marker(value: str) -> bool:
    return any(marker in value for marker in ("sign", "signature", "nonce", "timestamp"))
