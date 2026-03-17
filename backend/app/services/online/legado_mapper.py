import re
import json
from html import unescape
from typing import Any
from urllib.parse import parse_qsl

from app.schemas.legado_import import LegadoImportCode, LegadoMappedSource
from app.services.online.legado_validator import LegadoValidationReport


SEARCH_FIELD_MAP = {
    "name": "title",
    "bookName": "title",
    "bookUrl": "detail_url",
    "url": "detail_url",
    "author": "author",
    "intro": "description",
    "desc": "description",
    "description": "description",
    "coverUrl": "cover_url",
    "cover": "cover_url",
    "bookId": "remote_book_id",
    "id": "remote_book_id",
}
DETAIL_FIELD_MAP = {
    "name": "title",
    "bookName": "title",
    "author": "author",
    "intro": "description",
    "desc": "description",
    "description": "description",
    "coverUrl": "cover_url",
    "cover": "cover_url",
    "tocUrl": "catalog_url",
    "catalogUrl": "catalog_url",
    "chapterUrl": "catalog_url",
}
CATALOG_FIELD_MAP = {
    "chapterName": "chapter_title",
    "name": "chapter_title",
    "chapterUrl": "chapter_url",
    "url": "chapter_url",
}
ALLOWED_METHODS = {"GET", "POST"}
CSS_PREFIXES = ("css:", "jsoup:")
JSONPATH_PREFIXES = ("jsonpath:", "json:")
XPATH_PREFIXES = ("xpath:",)
REGEX_PREFIXES = ("regex:",)
COMMON_HTML_TAG_NAMES = {
    "a",
    "abbr",
    "address",
    "article",
    "aside",
    "audio",
    "b",
    "blockquote",
    "body",
    "button",
    "canvas",
    "code",
    "dd",
    "div",
    "dl",
    "dt",
    "em",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "html",
    "i",
    "img",
    "input",
    "label",
    "li",
    "main",
    "nav",
    "ol",
    "option",
    "p",
    "pre",
    "section",
    "select",
    "small",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


def map_legado_source(
    source: dict[str, Any],
    report: LegadoValidationReport,
) -> LegadoMappedSource | None:
    try:
        mapped_payload = {
            "name": _require_string(source, "bookSourceName", report),
            "description": _extract_optional_text(source.get("bookSourceComment")),
            "enabled": bool(source.get("enabled", True)),
            "base_url": _require_string(source, "bookSourceUrl", report),
            "definition": _build_definition(source, report),
        }
    except Exception as exc:  # pragma: no cover
        report.add_error(LegadoImportCode.MAPPING_FAILED, f"Unexpected mapping failure: {exc}", "source")
        return None

    if not report.is_valid:
        return None

    if not mapped_payload["name"] or not mapped_payload["base_url"] or not mapped_payload["definition"]:
        return None

    try:
        return LegadoMappedSource.model_validate(mapped_payload)
    except Exception as exc:
        report.add_error(LegadoImportCode.MAPPING_FAILED, f"Mapped source validation failed: {exc}", "source")
        return None


def _build_definition(source: dict[str, Any], report: LegadoValidationReport) -> dict[str, Any]:
    global_headers = _normalize_static_mapping(source.get("header"), report, "header")
    search_request = _parse_search_request(source.get("searchUrl"), report, global_headers)

    search_stage = {
        "request": search_request | {"response_type": _infer_stage_response_type(source.get("ruleSearch"))},
        "list_selector": _parse_list_selector(
            source.get("ruleSearch"),
            ("bookList", "list"),
            report,
            "ruleSearch.bookList",
        ),
        "fields": _parse_stage_fields(source.get("ruleSearch"), SEARCH_FIELD_MAP, report, "ruleSearch"),
    }
    detail_stage = {
        "request": {
            "method": "GET",
            "url": "{{detail_url}}",
            "response_type": _infer_stage_response_type(source.get("ruleBookInfo")),
            "headers": global_headers,
            "query": {},
            "body": {},
        },
        "fields": _parse_stage_fields(source.get("ruleBookInfo"), DETAIL_FIELD_MAP, report, "ruleBookInfo"),
    }
    catalog_stage = {
        "request": {
            "method": "GET",
            "url": "{{catalog_url}}",
            "response_type": _infer_stage_response_type(source.get("ruleToc")),
            "headers": global_headers,
            "query": {},
            "body": {},
        },
        "list_selector": _parse_list_selector(
            source.get("ruleToc"),
            ("chapterList", "list"),
            report,
            "ruleToc.chapterList",
        ),
        "fields": _parse_stage_fields(source.get("ruleToc"), CATALOG_FIELD_MAP, report, "ruleToc"),
    }
    content_stage = {
        "request": {
            "method": "GET",
            "url": "{{chapter_url}}",
            "response_type": _infer_stage_response_type(source.get("ruleContent")),
            "headers": global_headers,
            "query": {},
            "body": {},
        },
        "fields": _parse_stage_fields(source.get("ruleContent"), {"content": "content", "text": "content", "body": "content"}, report, "ruleContent"),
    }
    return {
        "search": search_stage,
        "detail": detail_stage,
        "catalog": catalog_stage,
        "content": content_stage,
    }


def _parse_search_request(
    raw_search_url: Any,
    report: LegadoValidationReport,
    global_headers: dict[str, str],
) -> dict[str, Any]:
    if not isinstance(raw_search_url, (str, dict)):
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            "searchUrl must be a string or object",
            "searchUrl",
        )
        return _empty_request()

    if isinstance(raw_search_url, dict):
        request_spec = raw_search_url
    else:
        request_spec = _parse_search_url_string(raw_search_url, report)

    raw_method = str(request_spec.get("method", "GET")).upper()
    if raw_method not in ALLOWED_METHODS:
        report.add_error(
            LegadoImportCode.UNSUPPORTED_METHOD,
            f"Unsupported method in searchUrl: {raw_method}",
            "searchUrl.method",
        )
        raw_method = "GET"

    normalized_headers = {
        **global_headers,
        **_normalize_static_mapping(request_spec.get("headers"), report, "searchUrl.headers"),
    }
    normalized_body = _normalize_body_mapping(request_spec.get("body"), report, "searchUrl.body")
    raw_url = _normalize_placeholders(str(request_spec.get("url", "")).strip(), report, "searchUrl.url")
    if not raw_url:
        report.add_error(
            LegadoImportCode.REQUIRED_FIELD_MISSING,
            "searchUrl.url is required",
            "searchUrl.url",
        )

    return {
        "method": raw_method,
        "url": raw_url,
        "headers": normalized_headers,
        "query": {},
        "body": normalized_body,
    }


def _parse_search_url_string(raw_search_url: str, report: LegadoValidationReport) -> dict[str, Any]:
    normalized = raw_search_url.strip()
    json_marker = ",{"
    if json_marker not in normalized:
        return {"url": normalized, "method": "GET"}

    json_start = normalized.find(json_marker)
    url_part = normalized[:json_start].strip()
    options_part = normalized[json_start + 1 :].strip()
    try:
        options = json.loads(options_part)
    except json.JSONDecodeError as exc:
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            f"Failed to parse searchUrl request options JSON: {exc.msg}",
            "searchUrl",
        )
        return {"url": url_part, "method": "GET"}

    if not isinstance(options, dict):
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            "searchUrl request options must decode to an object",
            "searchUrl",
        )
        return {"url": url_part, "method": "GET"}

    return {
        "url": url_part,
        "method": options.get("method", "GET"),
        "headers": options.get("headers") or options.get("header") or {},
        "body": options.get("body") or {},
    }


def _parse_stage_fields(
    raw_stage: Any,
    field_map: dict[str, str],
    report: LegadoValidationReport,
    stage_path: str,
) -> dict[str, Any]:
    if not isinstance(raw_stage, dict):
        report.add_error(LegadoImportCode.MAPPING_FAILED, f"{stage_path} must be an object", stage_path)
        return {}

    fields: dict[str, Any] = {}
    seen_targets: set[str] = set()
    for legacy_field_name, target_field_name in field_map.items():
        field_path = f"{stage_path}.{legacy_field_name}"
        if legacy_field_name not in raw_stage:
            continue
        if target_field_name in seen_targets:
            continue
        parsed_field = _parse_rule_expression(raw_stage[legacy_field_name], report, field_path, list_selector=False)
        if parsed_field is None:
            continue
        parsed_field["required"] = target_field_name in {"title", "detail_url", "catalog_url", "chapter_title", "chapter_url", "content"}
        fields[target_field_name] = parsed_field
        seen_targets.add(target_field_name)

    return fields


def _parse_list_selector(
    raw_stage: Any,
    legacy_field_names: tuple[str, ...],
    report: LegadoValidationReport,
    field_path: str,
) -> dict[str, Any] | None:
    if not isinstance(raw_stage, dict):
        report.add_error(LegadoImportCode.MAPPING_FAILED, f"{field_path.rsplit('.', 1)[0]} must be an object", field_path)
        return None

    raw_rule = None
    actual_field_path = field_path
    for legacy_field_name in legacy_field_names:
        if legacy_field_name in raw_stage:
            raw_rule = raw_stage.get(legacy_field_name)
            actual_field_path = f"{field_path.rsplit('.', 1)[0]}.{legacy_field_name}"
            break
    parsed_rule = _parse_rule_expression(raw_rule, report, actual_field_path, list_selector=True)
    if parsed_rule is None:
        return None
    return {
        "parser": parsed_rule["parser"],
        "expr": parsed_rule["expr"],
    }


def _parse_rule_expression(
    raw_rule: Any,
    report: LegadoValidationReport,
    field_path: str,
    *,
    list_selector: bool,
) -> dict[str, Any] | None:
    if not isinstance(raw_rule, str) or not raw_rule.strip():
        report.add_error(
            LegadoImportCode.REQUIRED_FIELD_MISSING,
            f"{field_path} is required",
            field_path,
        )
        return None

    normalized_rule = _normalize_placeholders(raw_rule.strip(), report, field_path)
    parser, expr = _detect_parser(normalized_rule)
    if parser is None:
        report.add_error(
            LegadoImportCode.UNSUPPORTED_PARSER,
            f"{field_path} does not use a supported parser prefix or expression",
            field_path,
        )
        return None

    if parser == "css":
        selector, attr = _parse_css_expression(expr)
        if not selector:
            report.add_error(
                LegadoImportCode.MAPPING_FAILED,
                f"{field_path} CSS selector is empty",
                field_path,
            )
            return None
        if list_selector:
            if attr not in {None, "text"}:
                report.add_error(
                    LegadoImportCode.MAPPING_FAILED,
                    f"{field_path} list selector cannot use CSS attribute extraction",
                    field_path,
                )
                return None
            return {"parser": "css", "expr": selector}
        if attr and _looks_like_nested_parser_expression(attr):
            report.add_error(
                LegadoImportCode.UNSUPPORTED_PARSER,
                f"{field_path} uses unsupported nested parser syntax: {attr}",
                field_path,
                raw_value=raw_rule,
            )
            return None
        field_definition = {"parser": "css", "expr": selector}
        if attr == "html":
            report.add_warning(
                LegadoImportCode.CSS_HTML_NORMALIZED,
                f"{field_path} uses @html and was normalized to the current CSS text-compatible form",
                field_path,
                raw_value=raw_rule,
                normalized_value={"parser": "css", "expr": selector},
            )
            return field_definition
        # Freeze Phase 2 behavior: selector@text maps to plain CSS text extraction,
        # so attr=text is intentionally omitted from the canonical definition.
        if attr and attr != "text":
            field_definition["attr"] = attr
        return field_definition

    if parser == "regex":
        regex_expr, regex_group = _parse_regex_expression(expr)
        field_definition = {"parser": "regex", "expr": regex_expr}
        if regex_group is not None:
            field_definition["regex_group"] = regex_group
        return field_definition

    if list_selector:
        return {"parser": parser, "expr": expr}

    return {"parser": parser, "expr": expr}


def _detect_parser(rule: str) -> tuple[str | None, str]:
    lowered_rule = rule.lower()
    for prefix in CSS_PREFIXES:
        if lowered_rule.startswith(prefix):
            return "css", rule[len(prefix) :].strip()
    for prefix in JSONPATH_PREFIXES:
        if lowered_rule.startswith(prefix):
            return "jsonpath", rule[len(prefix) :].strip()
    for prefix in XPATH_PREFIXES:
        if lowered_rule.startswith(prefix):
            return "xpath", rule[len(prefix) :].strip()
    for prefix in REGEX_PREFIXES:
        if lowered_rule.startswith(prefix):
            return "regex", rule[len(prefix) :].strip()

    if rule.startswith("$"):
        return "jsonpath", rule
    if rule.startswith("//") or rule.startswith("./") or rule.startswith(".//"):
        return "xpath", rule
    explicit_prefix = _extract_leading_prefix(rule)
    if explicit_prefix and explicit_prefix not in COMMON_HTML_TAG_NAMES:
        return None, rule
    return "css", rule


def _parse_css_expression(rule: str) -> tuple[str, str | None]:
    if "@" not in rule:
        return rule.strip(), None

    selector, suffix = rule.rsplit("@", 1)
    normalized_selector = selector.strip()
    normalized_suffix = suffix.strip()
    if not normalized_selector:
        return "", None
    if not normalized_suffix:
        return normalized_selector, None
    return normalized_selector, normalized_suffix


def _parse_regex_expression(rule: str) -> tuple[str, int | None]:
    if "##" not in rule:
        return rule.strip(), None

    expr, raw_group = rule.rsplit("##", 1)
    try:
        regex_group = int(raw_group.strip())
    except ValueError:
        return rule.strip(), None
    return expr.strip(), regex_group


def _extract_leading_prefix(rule: str) -> str | None:
    match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):", rule.strip())
    if not match:
        return None
    return match.group(1).lower()


def _looks_like_nested_parser_expression(attr: str) -> bool:
    lowered_attr = attr.strip().lower()
    return lowered_attr.startswith(("css:", "jsoup:", "json:", "jsonpath:", "xpath:", "regex:"))


def _normalize_static_mapping(value: Any, report: LegadoValidationReport, field_path: str) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            f"{field_path} must be an object of static key/value pairs",
            field_path,
        )
        return {}

    normalized_mapping: dict[str, str] = {}
    for item_key, item_value in value.items():
        normalized_key = str(item_key).strip()
        if not normalized_key:
            continue
        normalized_mapping[normalized_key] = _normalize_placeholders(str(item_value).strip(), report, f"{field_path}.{normalized_key}")
    return normalized_mapping


def _normalize_body_mapping(value: Any, report: LegadoValidationReport, field_path: str) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if isinstance(value, dict):
        return _normalize_static_mapping(value, report, field_path)
    if isinstance(value, str):
        normalized_body = _normalize_placeholders(value.strip(), report, field_path)
        return {
            key: mapped_value
            for key, mapped_value in (
                (key.strip(), value.strip())
                for key, value in parse_qsl(normalized_body, keep_blank_values=True)
            )
            if key
        }

    report.add_error(
        LegadoImportCode.MAPPING_FAILED,
        f"{field_path} must be a static object or query-string body",
        field_path,
    )
    return {}


def _normalize_placeholders(value: str, report: LegadoValidationReport, field_path: str) -> str:
    def _replace_placeholder(match):
        placeholder = match.group(1).strip()
        if placeholder == "key":
            return "{{keyword}}"
        if placeholder == "page":
            return "{{page}}"
        report.add_error(
            LegadoImportCode.UNSUPPORTED_PLACEHOLDER,
            f"{field_path} uses unsupported placeholder: {placeholder}",
            field_path,
        )
        return match.group(0)

    return re_placeholder.sub(_replace_placeholder, unescape(value))


def _require_string(source: dict[str, Any], field_name: str, report: LegadoValidationReport) -> str:
    value = source.get(field_name)
    if not isinstance(value, str) or not value.strip():
        report.add_error(
            LegadoImportCode.REQUIRED_FIELD_MISSING,
            f"{field_name} is required",
            field_name,
        )
        return ""
    return value.strip()


def _extract_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _infer_stage_response_type(stage_definition: Any) -> str:
    if not isinstance(stage_definition, dict):
        return "html"
    for rule in stage_definition.values():
        if not isinstance(rule, str):
            continue
        parser, _ = _detect_parser(rule.strip())
        if parser == "jsonpath":
            return "json"
    return "html"


def _empty_request() -> dict[str, Any]:
    return {
        "method": "GET",
        "url": "",
        "headers": {},
        "query": {},
        "body": {},
    }


re_placeholder = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
