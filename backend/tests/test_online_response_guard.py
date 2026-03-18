import httpx
import pytest

from app.schemas.online_runtime import LegadoRuntimeCode
from app.services.online.fetch_service import FetchServiceError, fetch_stage_response
from app.services.online.response_guard_service import classify_generic_response_issue, classify_transport_exception


def build_response(*, method: str = "GET", url: str = "https://example.com/search", status_code: int, content_type: str = "text/html; charset=utf-8", content: bytes | str = b"<html>ok</html>") -> httpx.Response:
    request = httpx.Request(method, url)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return httpx.Response(
        status_code=status_code,
        headers={"content-type": content_type},
        content=content,
        request=request,
    )


def test_classify_transport_exception_returns_timeout_issue():
    issue = classify_transport_exception(httpx.TimeoutException("timeout"), url="https://example.com/search")

    assert issue is not None
    assert issue.code == LegadoRuntimeCode.REQUEST_TIMEOUT
    assert "timeout" in issue.message.lower()


def test_classify_generic_response_returns_rate_limited_issue_for_429():
    issue = classify_generic_response_issue(
        build_response(status_code=429),
        url="https://example.com/search",
    )

    assert issue is not None
    assert issue.code == LegadoRuntimeCode.RATE_LIMITED
    assert "429" in issue.message


def test_classify_generic_response_returns_none_for_success_response():
    issue = classify_generic_response_issue(
        build_response(status_code=200),
        url="https://example.com/search",
    )

    assert issue is None


def test_fetch_stage_response_maps_timeout_to_legado_request_timeout(monkeypatch):
    def fake_request(**kwargs):
        raise httpx.TimeoutException("request timeout")

    monkeypatch.setattr(httpx, "request", fake_request)

    with pytest.raises(FetchServiceError) as exc_info:
        fetch_stage_response(
            method="GET",
            url="https://example.com/search",
            response_type="html",
        )

    assert exc_info.value.code == LegadoRuntimeCode.REQUEST_TIMEOUT
    assert "timeout" in str(exc_info.value).lower()


def test_fetch_stage_response_maps_429_to_legado_rate_limited(monkeypatch):
    def fake_request(**kwargs):
        return build_response(status_code=429)

    monkeypatch.setattr(httpx, "request", fake_request)

    with pytest.raises(FetchServiceError) as exc_info:
        fetch_stage_response(
            method="GET",
            url="https://example.com/search",
            response_type="html",
        )

    assert exc_info.value.code == LegadoRuntimeCode.RATE_LIMITED
    assert "429" in str(exc_info.value)


def test_fetch_stage_response_keeps_success_path_unchanged(monkeypatch):
    def fake_request(**kwargs):
        return build_response(status_code=200, content="<html><body>ok</body></html>")

    monkeypatch.setattr(httpx, "request", fake_request)

    response = fetch_stage_response(
        method="GET",
        url="https://example.com/search",
        response_type="html",
    )

    assert response.status_code == 200
    assert "ok" in response.text
