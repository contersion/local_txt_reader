import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from app.schemas.online_discovery import (
    ChapterContentPreview,
    LibraryBookDetailPreview,
    OnlineDiscoveryCatalogResponse,
    OnlineDiscoverySearchResponse,
)
from app.schemas.online_runtime import OnlineAuthConfig, SessionContext
from app.services.online.content_parse_service import (
    ContentParseError,
    parse_catalog_preview,
    parse_chapter_preview,
    parse_detail_preview,
    parse_search_preview,
)
from app.services.online.detector_gating_skeleton import evaluate_detector_behavior_gate_noop
from app.services.online.detector_live_entry_skeleton import (
    observe_live_entry_from_fetch_error,
    observe_live_entry_from_success_response,
)
from app.services.online.fetch_service import FetchServiceError, fetch_stage_response
from app.services.online.online_sources import get_online_source
from app.services.online.parser_engine import ParserEngineError
from app.services.online.request_profile_service import RequestProfileError, build_request_profile


class OnlineDiscoveryError(ValueError):
    pass


PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def preview_search(
    db,
    user_id: int,
    source_id: int,
    *,
    keyword: str,
    page: int,
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
) -> OnlineDiscoverySearchResponse:
    # ``auth_config`` / ``session_context`` are internal runtime hooks for the
    # Phase 3 skeleton. Current routers keep using the default path without
    # passing them, so existing preview APIs remain backward compatible.
    source = get_online_source(db, user_id, source_id)
    definition = _load_definition(source.definition_json)
    stage_definition = definition["search"]
    try:
        _ensure_supported_stage_parsers(stage_definition)
        stage_request = _build_stage_request(
            base_url=source.base_url,
            stage_definition=stage_definition,
            placeholders={"keyword": keyword, "page": str(page)},
        )
        raw_response = _execute_stage(
            stage="search",
            stage_request=stage_request,
            auth_config=auth_config,
            session_context=session_context,
        )
        return parse_search_preview(
            source_id=source.id,
            source_name=source.name,
            raw_response=raw_response,
            stage_definition=stage_definition,
        )
    except (FetchServiceError, ParserEngineError, ContentParseError, RequestProfileError) as exc:
        raise OnlineDiscoveryError(str(exc)) from exc


def preview_detail(
    db,
    user_id: int,
    source_id: int,
    *,
    detail_url: str,
    remote_book_id: str | None,
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
) -> LibraryBookDetailPreview:
    source = get_online_source(db, user_id, source_id)
    definition = _load_definition(source.definition_json)
    stage_definition = definition["detail"]
    try:
        _ensure_supported_stage_parsers(stage_definition)
        stage_request = _build_stage_request(
            base_url=source.base_url,
            stage_definition=stage_definition,
            placeholders={"detail_url": detail_url},
        )
        raw_response = _execute_stage(
            stage="detail",
            stage_request=stage_request,
            auth_config=auth_config,
            session_context=session_context,
        )
        return parse_detail_preview(
            source_id=source.id,
            source_name=source.name,
            raw_response=raw_response,
            stage_definition=stage_definition,
            detail_url=detail_url,
            remote_book_id=remote_book_id,
        )
    except (FetchServiceError, ParserEngineError, ContentParseError, RequestProfileError) as exc:
        raise OnlineDiscoveryError(str(exc)) from exc


def preview_catalog(
    db,
    user_id: int,
    source_id: int,
    *,
    catalog_url: str,
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
) -> OnlineDiscoveryCatalogResponse:
    source = get_online_source(db, user_id, source_id)
    definition = _load_definition(source.definition_json)
    stage_definition = definition["catalog"]
    try:
        _ensure_supported_stage_parsers(stage_definition)
        stage_request = _build_stage_request(
            base_url=source.base_url,
            stage_definition=stage_definition,
            placeholders={"catalog_url": catalog_url},
        )
        raw_response = _execute_stage(
            stage="catalog",
            stage_request=stage_request,
            auth_config=auth_config,
            session_context=session_context,
        )
        return parse_catalog_preview(
            raw_response=raw_response,
            stage_definition=stage_definition,
        )
    except (FetchServiceError, ParserEngineError, ContentParseError, RequestProfileError) as exc:
        raise OnlineDiscoveryError(str(exc)) from exc


def preview_chapter(
    db,
    user_id: int,
    source_id: int,
    *,
    chapter_url: str,
    chapter_index: int,
    chapter_title: str | None,
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
) -> ChapterContentPreview:
    source = get_online_source(db, user_id, source_id)
    definition = _load_definition(source.definition_json)
    stage_definition = definition["content"]
    try:
        _ensure_supported_stage_parsers(stage_definition)
        stage_request = _build_stage_request(
            base_url=source.base_url,
            stage_definition=stage_definition,
            placeholders={"chapter_url": chapter_url},
        )
        raw_response = _execute_stage(
            stage="content",
            stage_request=stage_request,
            auth_config=auth_config,
            session_context=session_context,
        )
        return parse_chapter_preview(
            raw_response=raw_response,
            stage_definition=stage_definition,
            chapter_url=chapter_url,
            chapter_index=chapter_index,
            chapter_title=chapter_title,
        )
    except (FetchServiceError, ParserEngineError, ContentParseError, RequestProfileError) as exc:
        raise OnlineDiscoveryError(str(exc)) from exc


def _load_definition(definition_json: str) -> dict[str, Any]:
    try:
        return json.loads(definition_json)
    except json.JSONDecodeError as exc:
        raise OnlineDiscoveryError("Saved source definition is invalid JSON") from exc


def _build_stage_request(
    *,
    base_url: str,
    stage_definition: dict[str, Any],
    placeholders: dict[str, str],
) -> dict[str, Any]:
    request_definition = stage_definition["request"]
    rendered_url = _render_string(request_definition["url"], placeholders)
    resolved_url = _resolve_runtime_url(base_url, rendered_url)
    return {
        "method": request_definition["method"],
        "url": resolved_url,
        "response_type": request_definition["response_type"],
        "headers": _render_mapping(request_definition.get("headers", {}), placeholders),
        "query": _render_mapping(request_definition.get("query", {}), placeholders),
        "body": _render_mapping(request_definition.get("body", {}), placeholders),
    }


def _execute_stage(
    stage: str,
    stage_request: dict[str, Any],
    *,
    auth_config: OnlineAuthConfig | None = None,
    session_context: SessionContext | None = None,
):
    # Optional runtime injection is assembled here so the public router/API
    # surface can remain unchanged while Phase 3 is still only a skeleton.
    request_profile = build_request_profile(
        stage_request=stage_request,
        auth_config=auth_config,
        session_context=session_context,
    )
    try:
        raw_response = fetch_stage_response(
            method=request_profile.method,
            url=request_profile.url,
            response_type=request_profile.response_type,
            headers=request_profile.headers,
            query=request_profile.query,
            body=request_profile.body,
            cookies=request_profile.cookies,
        )
    except FetchServiceError as exc:
        # Internal-only live-entry skeleton. The observation result is
        # intentionally discarded so Phase 3-B.14 can prove wiring exists
        # without changing error surfaces or public behavior.
        _observe_live_entry_error_noop(
            stage=stage,
            expected_response_type=request_profile.response_type,
            requested_url=request_profile.url,
            error=exc,
        )
        raise

    # Internal-only live-entry skeleton. The observation result is
    # intentionally discarded so parser/API behavior stays unchanged.
    _observe_live_entry_success_noop(
        stage=stage,
        expected_response_type=request_profile.response_type,
        raw_response=raw_response,
    )
    return raw_response


def _observe_live_entry_success_noop(*, stage: str, expected_response_type: str, raw_response) -> None:
    try:
        adapter_output = observe_live_entry_from_success_response(
            stage=stage,
            expected_response_type=expected_response_type,
            raw_response=raw_response,
        )
        _ = evaluate_detector_behavior_gate_noop(adapter_output)
    except Exception:
        # The live-entry skeleton is internal observation only. Any failure in
        # this branch must not change the existing fetch -> parser behavior.
        return


def _observe_live_entry_error_noop(
    *,
    stage: str,
    expected_response_type: str,
    requested_url: str,
    error: FetchServiceError,
) -> None:
    try:
        adapter_output = observe_live_entry_from_fetch_error(
            stage=stage,
            expected_response_type=expected_response_type,
            requested_url=requested_url,
            error=error,
        )
        _ = evaluate_detector_behavior_gate_noop(adapter_output)
    except Exception:
        # The live-entry skeleton is internal observation only. Any failure in
        # this branch must not change the existing error surface.
        return


def _render_mapping(mapping: dict[str, str], placeholders: dict[str, str]) -> dict[str, str]:
    return {key: _render_string(value, placeholders) for key, value in mapping.items()}


def _render_string(value: str, placeholders: dict[str, str]) -> str:
    def _replace(match: re.Match) -> str:
        placeholder = match.group(1)
        if placeholder not in placeholders:
            raise OnlineDiscoveryError(f"Missing runtime placeholder value: {placeholder}")
        return placeholders[placeholder]

    return PLACEHOLDER_PATTERN.sub(_replace, value)


def _resolve_runtime_url(base_url: str, rendered_url: str) -> str:
    resolved_url = urljoin(f"{base_url}/", rendered_url)
    parsed_url = urlparse(resolved_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise OnlineDiscoveryError(f"Runtime URL must use http/https: {rendered_url}")
    return resolved_url


def _ensure_supported_stage_parsers(stage_definition: dict[str, Any]) -> None:
    supported_parsers = {"css", "jsonpath", "xpath", "regex"}
    list_selector = stage_definition.get("list_selector")
    if list_selector and list_selector.get("parser") not in supported_parsers:
        raise OnlineDiscoveryError(f"Unsupported parser: {list_selector.get('parser')}")

    for field_definition in stage_definition.get("fields", {}).values():
        parser_name = field_definition.get("parser")
        if parser_name not in supported_parsers:
            raise OnlineDiscoveryError(f"Unsupported parser: {parser_name}")
