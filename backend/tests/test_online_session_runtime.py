from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.schemas.online_runtime import (
    LegadoRuntimeCode,
    OnlineAuthConfig,
    OnlineAuthMode,
    SessionContext,
    SessionCookie,
)
from app.services.online.fetch_service import fetch_stage_response
from app.services.online.request_profile_service import RequestProfileError, build_request_profile
from app.services.online.session_handler import InMemorySessionStorage, SessionHandler


def build_stage_request():
    return {
        "method": "GET",
        "url": "https://example.com/books",
        "response_type": "html",
        "headers": {"User-Agent": "TXT-Reader-Test/1.0"},
        "query": {"q": "三体"},
        "body": {},
    }


def build_session_context(**overrides):
    payload = {
        "session_id": "session-1",
        "user_id": 1,
        "source_id": 2,
        "headers": {"X-Session": "runtime-token"},
        "cookies": [
            {
                "name": "sid",
                "value": "cookie-value",
            }
        ],
        "authenticated_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    payload.update(overrides)
    return SessionContext.model_validate(payload)


def test_session_handler_round_trip_resolves_saved_context():
    storage = InMemorySessionStorage()
    handler = SessionHandler(storage=storage)
    context = build_session_context()

    handler.save_context(context)

    resolved = handler.resolve_context(
        OnlineAuthConfig(
            mode=OnlineAuthMode.SESSION,
            login_required=True,
            session_id=context.session_id,
        )
    )

    assert resolved is not None
    assert resolved.session_id == context.session_id
    assert resolved.headers["X-Session"] == "runtime-token"
    assert resolved.cookies[0].name == "sid"


def test_session_handler_resolve_context_returns_none_for_expired_session():
    storage = InMemorySessionStorage()
    handler = SessionHandler(storage=storage)
    expired_context = build_session_context(
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    handler.save_context(expired_context)

    resolved = handler.resolve_context(
        OnlineAuthConfig(
            mode=OnlineAuthMode.SESSION,
            login_required=True,
            session_id=expired_context.session_id,
        )
    )

    assert resolved is None


def test_session_handler_resolve_context_returns_none_for_user_id_mismatch():
    storage = InMemorySessionStorage()
    handler = SessionHandler(storage=storage)
    context = build_session_context(user_id=7, source_id=9)
    handler.save_context(context)

    resolved = handler.resolve_context(
        OnlineAuthConfig(
            mode=OnlineAuthMode.SESSION,
            login_required=True,
            session_id=context.session_id,
        ),
        user_id=8,
    )

    assert resolved is None


def test_session_handler_resolve_context_returns_none_for_source_id_mismatch():
    storage = InMemorySessionStorage()
    handler = SessionHandler(storage=storage)
    context = build_session_context(user_id=7, source_id=9)
    handler.save_context(context)

    resolved = handler.resolve_context(
        OnlineAuthConfig(
            mode=OnlineAuthMode.SESSION,
            login_required=True,
            session_id=context.session_id,
        ),
        source_id=10,
    )

    assert resolved is None


def test_session_handler_overwrite_and_clear_context():
    storage = InMemorySessionStorage()
    handler = SessionHandler(storage=storage)
    initial_context = build_session_context(headers={"X-Session": "old-token"})
    updated_context = build_session_context(headers={"X-Session": "new-token"})

    handler.save_context(initial_context)
    handler.save_context(updated_context)

    resolved = handler.resolve_context(
        OnlineAuthConfig(
            mode=OnlineAuthMode.SESSION,
            login_required=True,
            session_id=updated_context.session_id,
        )
    )

    assert resolved is not None
    assert resolved.headers["X-Session"] == "new-token"

    handler.clear_context(updated_context.session_id)

    assert handler.resolve_context(session_id=updated_context.session_id) is None


def test_build_request_profile_without_session_keeps_request_unchanged():
    stage_request = build_stage_request()

    profile = build_request_profile(
        stage_request=stage_request,
        auth_config=None,
        session_context=None,
    )

    assert profile.method == stage_request["method"]
    assert profile.url == stage_request["url"]
    assert profile.response_type == stage_request["response_type"]
    assert profile.headers == stage_request["headers"]
    assert profile.query == stage_request["query"]
    assert profile.body == stage_request["body"]
    assert profile.cookies == {}


def test_build_request_profile_injects_session_headers_and_cookies():
    stage_request = build_stage_request()
    context = build_session_context(
        headers={"X-Session": "runtime-token", "User-Agent": "should-not-win"},
        cookies=[
            SessionCookie(name="sid", value="cookie-value"),
            SessionCookie(
                name="theme",
                value="dark",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ),
        ],
    )

    profile = build_request_profile(
        stage_request=stage_request,
        auth_config=OnlineAuthConfig(mode=OnlineAuthMode.SESSION, login_required=True),
        session_context=context,
    )

    assert profile.headers["User-Agent"] == "TXT-Reader-Test/1.0"
    assert profile.headers["X-Session"] == "runtime-token"
    assert profile.cookies == {"sid": "cookie-value", "theme": "dark"}


def test_build_request_profile_skips_blank_session_values():
    stage_request = build_stage_request()
    context = build_session_context(
        headers={"X-Session": "runtime-token", "X-Blank": "   "},
        cookies=[
            SessionCookie(name="sid", value="cookie-value"),
            SessionCookie(
                name="expired",
                value="stale",
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            ),
        ],
    )

    profile = build_request_profile(
        stage_request=stage_request,
        auth_config=OnlineAuthConfig(mode=OnlineAuthMode.SESSION, login_required=True),
        session_context=context,
    )

    assert profile.headers["X-Session"] == "runtime-token"
    assert "X-Blank" not in profile.headers
    assert profile.cookies == {"sid": "cookie-value"}


def test_build_request_profile_rejects_missing_session_when_auth_is_required():
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(),
            auth_config=OnlineAuthConfig(mode=OnlineAuthMode.SESSION, login_required=True),
            session_context=None,
        )

    assert exc_info.value.code == LegadoRuntimeCode.SESSION_MISSING


def test_build_request_profile_rejects_expired_session_context():
    expired_context = build_session_context(
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(),
            auth_config=OnlineAuthConfig(mode=OnlineAuthMode.SESSION, login_required=True),
            session_context=expired_context,
        )

    assert exc_info.value.code == LegadoRuntimeCode.SESSION_EXPIRED


def test_build_request_profile_rejects_invalid_auth_config():
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(),
            auth_config=OnlineAuthConfig(mode=OnlineAuthMode.TOKEN, login_required=False),
            session_context=None,
        )

    assert exc_info.value.code == LegadoRuntimeCode.AUTH_CONFIG_INVALID


def test_fetch_stage_response_passes_cookies_to_httpx_request(monkeypatch):
    captured_kwargs: dict[str, object] = {}

    def fake_request(*, method, url, headers, params, data, cookies, timeout, follow_redirects):
        captured_kwargs.update(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "data": data,
                "cookies": cookies,
                "timeout": timeout,
                "follow_redirects": follow_redirects,
            }
        )
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><body>ok</body></html>",
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    response = fetch_stage_response(
        method="GET",
        url="https://example.com/books",
        response_type="html",
        headers={"X-Test": "1"},
        cookies={"sid": "cookie-value"},
    )

    assert response.status_code == 200
    assert captured_kwargs["cookies"] == {"sid": "cookie-value"}
