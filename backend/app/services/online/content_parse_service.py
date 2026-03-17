from html import unescape
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.schemas.online_discovery import (
    CatalogItemPreview,
    ChapterContentPreview,
    LibraryBookDetailPreview,
    OnlineCatalogSourceLocator,
    OnlineChapterSourceLocator,
    OnlineDiscoveryCatalogResponse,
    OnlineDiscoverySearchResponse,
    OnlinePreviewFields,
    OnlineSearchResultPreview,
)
from app.services.online.fetch_service import RawFetchResponse
from app.services.online.parser_engine import extract_value, select_many


class ContentParseError(ValueError):
    pass


def parse_search_preview(
    *,
    source_id: int,
    source_name: str,
    raw_response: RawFetchResponse,
    stage_definition: dict[str, Any],
) -> OnlineDiscoverySearchResponse:
    list_selector = stage_definition.get("list_selector")
    if not list_selector:
        raise ContentParseError("search stage requires list_selector")

    item_contexts = select_many(
        raw_response,
        parser=list_selector["parser"],
        expr=list_selector["expr"],
    )
    items = []
    for item_context in item_contexts:
        items.append(
            OnlineSearchResultPreview.model_validate(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "remote_book_id": _extract_field(raw_response, item_context, stage_definition, "remote_book_id"),
                    "title": _extract_required_field(raw_response, item_context, stage_definition, "title"),
                    "author": _extract_field(raw_response, item_context, stage_definition, "author"),
                    "description": _extract_field(raw_response, item_context, stage_definition, "description"),
                    "cover_url": _normalize_optional_url(
                        _extract_field(raw_response, item_context, stage_definition, "cover_url"),
                        raw_response.final_url,
                    ),
                    "detail_url": _normalize_required_url(
                        _extract_required_field(raw_response, item_context, stage_definition, "detail_url"),
                        raw_response.final_url,
                        "detail_url",
                    ),
                }
            )
        )
    return OnlineDiscoverySearchResponse.model_validate({"items": items})


def parse_detail_preview(
    *,
    source_id: int,
    source_name: str,
    raw_response: RawFetchResponse,
    stage_definition: dict[str, Any],
    detail_url: str,
    remote_book_id: str | None,
) -> LibraryBookDetailPreview:
    title = _extract_required_field(raw_response, None, stage_definition, "title")
    catalog_url = _normalize_required_url(
        _extract_required_field(raw_response, None, stage_definition, "catalog_url"),
        raw_response.final_url,
        "catalog_url",
    )
    return LibraryBookDetailPreview.model_validate(
        {
            "source_label": source_name,
            "title": title,
            "author": _extract_field(raw_response, None, stage_definition, "author"),
            "description": _extract_field(raw_response, None, stage_definition, "description"),
            "cover_url": _normalize_optional_url(
                _extract_field(raw_response, None, stage_definition, "cover_url"),
                raw_response.final_url,
            ),
            "online_fields": OnlinePreviewFields.model_validate(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "detail_url": detail_url,
                    "catalog_url": catalog_url,
                    "remote_book_id": remote_book_id,
                }
            ),
        }
    )


def parse_catalog_preview(
    *,
    raw_response: RawFetchResponse,
    stage_definition: dict[str, Any],
) -> OnlineDiscoveryCatalogResponse:
    list_selector = stage_definition.get("list_selector")
    if not list_selector:
        raise ContentParseError("catalog stage requires list_selector")

    item_contexts = select_many(
        raw_response,
        parser=list_selector["parser"],
        expr=list_selector["expr"],
    )
    items = []
    for index, item_context in enumerate(item_contexts):
        chapter_title = _extract_required_field(raw_response, item_context, stage_definition, "chapter_title")
        chapter_url = _normalize_required_url(
            _extract_required_field(raw_response, item_context, stage_definition, "chapter_url"),
            raw_response.final_url,
            "chapter_url",
        )
        items.append(
            CatalogItemPreview.model_validate(
                {
                    "chapter_index": index,
                    "chapter_title": chapter_title,
                    "source_locator": OnlineCatalogSourceLocator.model_validate({"url": chapter_url}),
                }
            )
        )
    return OnlineDiscoveryCatalogResponse.model_validate({"items": items})


def parse_chapter_preview(
    *,
    raw_response: RawFetchResponse,
    stage_definition: dict[str, Any],
    chapter_url: str,
    chapter_index: int,
    chapter_title: str | None,
) -> ChapterContentPreview:
    raw_content = _extract_required_field(raw_response, None, stage_definition, "content")
    resolved_title = chapter_title.strip() if isinstance(chapter_title, str) and chapter_title.strip() else f"第 {chapter_index + 1} 章"
    return ChapterContentPreview.model_validate(
        {
            "chapter_index": chapter_index,
            "chapter_title": resolved_title,
            "content": _clean_text(raw_content),
            "source_locator": OnlineChapterSourceLocator.model_validate({"url": chapter_url}),
        }
    )


def _extract_required_field(
    raw_response: RawFetchResponse,
    context: Any | None,
    stage_definition: dict[str, Any],
    field_name: str,
) -> str:
    value = _extract_field(raw_response, context, stage_definition, field_name)
    if not value:
        raise ContentParseError(f"Missing required field: {field_name}")
    return value


def _extract_field(
    raw_response: RawFetchResponse,
    context: Any | None,
    stage_definition: dict[str, Any],
    field_name: str,
) -> str | None:
    field_definition = stage_definition.get("fields", {}).get(field_name)
    if not field_definition:
        return None
    return extract_value(
        raw_response,
        parser=field_definition["parser"],
        expr=field_definition["expr"],
        context=context,
        attr=field_definition.get("attr"),
        regex_group=field_definition.get("regex_group"),
    )


def _normalize_required_url(value: str, base_url: str, field_name: str) -> str:
    normalized = _normalize_optional_url(value, base_url)
    if not normalized:
        raise ContentParseError(f"Missing required field: {field_name}")
    return normalized


def _normalize_optional_url(value: str | None, base_url: str) -> str | None:
    if not value:
        return None
    return urljoin(base_url, value)


def _clean_text(value: str) -> str:
    text = value
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text("\n")
    text = unescape(text)
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized_lines: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if previous_blank:
                continue
            normalized_lines.append("")
            previous_blank = True
            continue
        normalized_lines.append(line)
        previous_blank = False
    return "\n".join(normalized_lines).strip()
