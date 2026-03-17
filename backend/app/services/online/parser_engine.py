import re
from typing import Any

from bs4 import BeautifulSoup, Tag
from jsonpath_ng.ext import parse as jsonpath_parse
from lxml import html as lxml_html
from lxml.html import HtmlElement

from app.services.online.fetch_service import RawFetchResponse


class ParserEngineError(ValueError):
    pass


def select_many(
    response: RawFetchResponse,
    *,
    parser: str,
    expr: str,
    context: Any | None = None,
) -> list[Any]:
    normalized_parser = parser.strip().lower()
    if normalized_parser == "css":
        scope = _resolve_css_scope(response, context)
        return list(scope.select(expr))
    if normalized_parser == "jsonpath":
        data = _resolve_json_scope(response, context)
        compiled = _compile_jsonpath(expr, allow_relative=context is not None)
        return [match.value for match in compiled.find(data)]
    if normalized_parser == "xpath":
        scope = _resolve_xpath_scope(response, context)
        return list(scope.xpath(expr))
    if normalized_parser == "regex":
        text = _resolve_regex_scope(response, context)
        return list(re.finditer(expr, text, re.DOTALL))
    raise ParserEngineError(f"Unsupported parser: {parser}")


def extract_value(
    response: RawFetchResponse,
    *,
    parser: str,
    expr: str,
    context: Any | None = None,
    attr: str | None = None,
    regex_group: int | None = None,
) -> str | None:
    matches = select_many(response, parser=parser, expr=expr, context=context)
    if not matches:
        return None

    first_match = matches[0]
    normalized_parser = parser.strip().lower()
    if normalized_parser == "css":
        return _extract_css_value(first_match, attr)
    if normalized_parser == "jsonpath":
        return _normalize_scalar_value(first_match)
    if normalized_parser == "xpath":
        return _extract_xpath_value(first_match, attr)
    if normalized_parser == "regex":
        return _extract_regex_value(first_match, regex_group)
    raise ParserEngineError(f"Unsupported parser: {parser}")


def _resolve_css_scope(response: RawFetchResponse, context: Any | None):
    if context is None:
        return BeautifulSoup(response.text, "html.parser")
    if isinstance(context, (BeautifulSoup, Tag)):
        return context
    raise ParserEngineError("CSS parser requires HTML context")


def _resolve_json_scope(response: RawFetchResponse, context: Any | None):
    data = context if context is not None else response.json_data
    if data is None:
        raise ParserEngineError("JSONPath parser requires JSON response data")
    return data


def _resolve_xpath_scope(response: RawFetchResponse, context: Any | None):
    if context is None:
        return lxml_html.fromstring(response.text)
    if isinstance(context, HtmlElement):
        return context
    raise ParserEngineError("XPath parser requires HTML/XPath context")


def _resolve_regex_scope(response: RawFetchResponse, context: Any | None) -> str:
    if context is None:
        return response.text
    if isinstance(context, str):
        return context
    raise ParserEngineError("Regex parser requires text context")


def _compile_jsonpath(expr: str, *, allow_relative: bool):
    normalized_expr = expr.strip()
    if allow_relative and not normalized_expr.startswith("$"):
        normalized_expr = f"$.{normalized_expr.lstrip('.')}"
    try:
        return jsonpath_parse(normalized_expr)
    except Exception as exc:  # pragma: no cover
        raise ParserEngineError(f"Invalid JSONPath expression: {expr}") from exc


def _extract_css_value(node: Any, attr: str | None) -> str | None:
    if not isinstance(node, Tag):
        raise ParserEngineError("CSS extraction target is not a tag")
    if attr:
        return _normalize_scalar_value(node.get(attr))
    return _normalize_scalar_value(node.get_text(" ", strip=True))


def _extract_xpath_value(node: Any, attr: str | None) -> str | None:
    if isinstance(node, HtmlElement):
        if attr:
            return _normalize_scalar_value(node.get(attr))
        return _normalize_scalar_value(node.text_content())
    if attr:
        return None
    return _normalize_scalar_value(node)


def _extract_regex_value(match: Any, regex_group: int | None) -> str | None:
    if not isinstance(match, re.Match):
        raise ParserEngineError("Regex extraction target is not a match object")
    try:
        value = match.group(regex_group or 0)
    except IndexError as exc:
        raise ParserEngineError(f"Regex group {regex_group} does not exist") from exc
    return _normalize_scalar_value(value)


def _normalize_scalar_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    normalized = str(value).strip()
    return normalized or None
