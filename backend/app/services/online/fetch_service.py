from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class FetchServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RawFetchResponse:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    text: str
    json_data: Any | None


def fetch_stage_response(
    *,
    method: str,
    url: str,
    response_type: str,
    headers: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
    body: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> RawFetchResponse:
    # Phase 3-A.1 keeps cookies as an optional runtime hook only.
    # This function does not own login orchestration, cookie refresh, or
    # persistence; it simply executes the final request profile it receives.
    _validate_runtime_url(url)
    request_headers = _merge_request_headers(headers)

    try:
        response = httpx.request(
            method=method,
            url=url,
            headers=request_headers,
            params=query or None,
            data=body or None,
            cookies=cookies or None,
            timeout=settings.online_request_timeout_seconds,
            follow_redirects=settings.online_follow_redirects,
        )
    except httpx.TimeoutException as exc:
        raise FetchServiceError(f"Request timeout while fetching {url}") from exc
    except httpx.InvalidURL as exc:
        raise FetchServiceError(f"Invalid runtime URL: {url}") from exc
    except httpx.RequestError as exc:
        raise FetchServiceError(f"Request failed for {url}: {exc}") from exc

    response_size = len(response.content)
    if response_size > settings.online_response_size_limit_bytes:
        raise FetchServiceError(
            f"Response too large: {response_size} bytes exceeds limit {settings.online_response_size_limit_bytes}"
        )

    if response.status_code >= 400:
        raise FetchServiceError(f"Remote request failed with status {response.status_code} for {url}")

    content_type = (response.headers.get("content-type") or "").lower()
    _validate_response_type(content_type, response_type)

    if response_type == "json":
        try:
            json_data = response.json()
        except ValueError as exc:
            raise FetchServiceError(f"Failed to decode JSON response from {url}") from exc
        text = response.text
    else:
        json_data = None
        text = response.text

    return RawFetchResponse(
        requested_url=url,
        final_url=str(response.url),
        status_code=response.status_code,
        content_type=content_type,
        text=text,
        json_data=json_data,
    )


def _validate_runtime_url(url: str) -> None:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise FetchServiceError(f"Runtime URL must use http/https: {url}")


def _validate_response_type(content_type: str, expected_response_type: str) -> None:
    if expected_response_type == "json":
        if "application/json" not in content_type and "+json" not in content_type:
            raise FetchServiceError(
                f"Response type mismatch: expected json but got {content_type or 'unknown'}"
            )
        return

    html_like_content_types = ("text/html", "application/xhtml+xml", "application/xml", "text/xml")
    if not any(item in content_type for item in html_like_content_types):
        raise FetchServiceError(
            f"Response type mismatch: expected html but got {content_type or 'unknown'}"
        )


def _merge_request_headers(headers: dict[str, str] | None) -> dict[str, str]:
    merged_headers = dict(headers or {})
    if not any(header_name.lower() == "user-agent" for header_name in merged_headers):
        merged_headers["User-Agent"] = settings.online_default_user_agent
    return merged_headers
