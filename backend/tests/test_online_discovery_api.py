import json
from contextlib import contextmanager

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models.online_source import OnlineSource


ONLINE_SOURCE_DEFINITION = {
    "search": {
        "request": {
            "method": "GET",
            "url": "/search?q={{keyword}}&page={{page}}",
            "response_type": "html",
            "headers": {
                "User-Agent": "TXT-Reader-Test/1.0",
            },
        },
        "list_selector": {
            "parser": "css",
            "expr": ".result-item",
        },
        "fields": {
            "remote_book_id": {
                "parser": "css",
                "expr": "a.title",
                "attr": "data-book-id",
                "required": True,
            },
            "title": {
                "parser": "css",
                "expr": "a.title",
                "required": True,
            },
            "detail_url": {
                "parser": "css",
                "expr": "a.title",
                "attr": "href",
                "required": True,
            },
            "author": {
                "parser": "css",
                "expr": ".author",
            },
            "cover_url": {
                "parser": "css",
                "expr": "img.cover",
                "attr": "src",
            },
        },
    },
    "detail": {
        "request": {
            "method": "GET",
            "url": "{{detail_url}}",
            "response_type": "json",
        },
        "fields": {
            "title": {
                "parser": "jsonpath",
                "expr": "$.book.title",
                "required": True,
            },
            "author": {
                "parser": "jsonpath",
                "expr": "$.book.author",
            },
            "description": {
                "parser": "jsonpath",
                "expr": "$.book.description",
            },
            "cover_url": {
                "parser": "jsonpath",
                "expr": "$.book.cover",
            },
            "catalog_url": {
                "parser": "jsonpath",
                "expr": "$.book.catalog_url",
                "required": True,
            },
        },
    },
    "catalog": {
        "request": {
            "method": "GET",
            "url": "{{catalog_url}}",
            "response_type": "html",
        },
        "list_selector": {
            "parser": "xpath",
            "expr": "//li[@class='chapter-item']",
        },
        "fields": {
            "chapter_title": {
                "parser": "xpath",
                "expr": "./a/text()",
                "required": True,
            },
            "chapter_url": {
                "parser": "xpath",
                "expr": "./a/@href",
                "required": True,
            },
        },
    },
    "content": {
        "request": {
            "method": "GET",
            "url": "{{chapter_url}}",
            "response_type": "html",
        },
        "fields": {
            "content": {
                "parser": "regex",
                "expr": "<div id=\"content\">([\\s\\S]+?)</div>",
                "regex_group": 1,
                "required": True,
            },
        },
    },
}


@contextmanager
def authenticated_client(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "default_admin_username", "admin")
    monkeypatch.setattr(settings, "default_admin_password", "admin123")
    monkeypatch.setattr(settings, "secret_key", "test-secret-key")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    with TestClient(create_application()) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        yield client


def create_source(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "预览书源",
        "description": "用于 stateless 预览测试",
        "enabled": True,
        "base_url": "https://example.com",
        "definition": ONLINE_SOURCE_DEFINITION,
    }
    payload.update(overrides)
    response = client.post("/api/online-sources", json=payload)
    assert response.status_code == 201
    return response.json()


def insert_source_directly(user_id: int, name: str, definition: dict) -> int:
    session = database.create_session()
    try:
        source = OnlineSource(
            user_id=user_id,
            name=name,
            description="direct insert",
            enabled=True,
            base_url="https://example.com",
            definition_json=json.dumps(definition, ensure_ascii=False, separators=(",", ":")),
            validation_status="valid",
            validation_errors_json="[]",
        )
        session.add(source)
        session.commit()
        session.refresh(source)
        return source.id
    finally:
        session.close()


def get_admin_user_id() -> int:
    session = database.create_session()
    try:
        return int(session.execute(text("SELECT id FROM users WHERE username = 'admin'")).scalar_one())
    finally:
        session.close()


def stub_httpx_request(monkeypatch, responses_by_url: dict[str, httpx.Response | Exception]):
    def _request(method: str, url: str, **kwargs):
        response_or_error = responses_by_url[url]
        if isinstance(response_or_error, Exception):
            raise response_or_error
        return response_or_error

    monkeypatch.setattr(httpx, "request", _request)


def build_response(method: str, url: str, *, status_code: int = 200, headers: dict[str, str] | None = None, content: bytes | str = b"") -> httpx.Response:
    request = httpx.Request(method, url)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return httpx.Response(status_code=status_code, headers=headers, content=content, request=request)


def test_search_preview_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        search_url = "https://example.com/search?q=三体&page=1"
        stub_httpx_request(
            monkeypatch,
            {
                search_url: build_response(
                    "GET",
                    search_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div class="result-item">
                        <a class="title" href="/books/1" data-book-id="book-1">三体</a>
                        <span class="author">刘慈欣</span>
                        <img class="cover" src="/covers/1.jpg" />
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source["id"], "keyword": "三体", "page": 1},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["title"] == "三体"
    assert payload["items"][0]["remote_book_id"] == "book-1"
    assert payload["items"][0]["detail_url"] == "https://example.com/books/1"


def test_detail_preview_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        detail_url = "https://example.com/books/1"
        stub_httpx_request(
            monkeypatch,
            {
                detail_url: build_response(
                    "GET",
                    detail_url,
                    headers={"content-type": "application/json"},
                    content=json.dumps(
                        {
                            "book": {
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
                                "cover": "https://example.com/covers/1.jpg",
                                "catalog_url": "https://example.com/books/1/catalog",
                            }
                        }
                    ),
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/detail",
            json={"source_id": source["id"], "detail_url": detail_url, "remote_book_id": "book-1"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "三体"
    assert payload["online_fields"]["catalog_url"] == "https://example.com/books/1/catalog"


def test_catalog_preview_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        catalog_url = "https://example.com/books/1/catalog"
        stub_httpx_request(
            monkeypatch,
            {
                catalog_url: build_response(
                    "GET",
                    catalog_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <ul>
                        <li class="chapter-item"><a href="/books/1/ch1">第一章 开始</a></li>
                        <li class="chapter-item"><a href="/books/1/ch2">第二章 夜航</a></li>
                      </ul>
                    </body></html>
                    """,
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/catalog",
            json={"source_id": source["id"], "catalog_url": catalog_url},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["chapter_index"] == 0
    assert payload["items"][0]["chapter_title"] == "第一章 开始"
    assert payload["items"][0]["source_locator"]["url"] == "https://example.com/books/1/ch1"


def test_chapter_preview_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        chapter_url = "https://example.com/books/1/ch1"
        stub_httpx_request(
            monkeypatch,
            {
                chapter_url: build_response(
                    "GET",
                    chapter_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div id="content">
                        第一段<br/>
                        第二段
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/chapter",
            json={
                "source_id": source["id"],
                "chapter_url": chapter_url,
                "chapter_index": 0,
                "chapter_title": "第一章 开始",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["chapter_index"] == 0
    assert payload["chapter_title"] == "第一章 开始"
    assert "第一段" in payload["content"]
    assert payload["content_format"] == "plain_text"


def test_discovery_rejects_unsupported_parser_even_if_source_exists(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        user_id = get_admin_user_id()
        invalid_definition = {
            **ONLINE_SOURCE_DEFINITION,
            "search": {
                **ONLINE_SOURCE_DEFINITION["search"],
                "list_selector": {
                    "parser": "unsupported",
                    "expr": ".result-item",
                },
            },
        }
        source_id = insert_source_directly(user_id, "坏书源", invalid_definition)

        response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source_id, "keyword": "三体", "page": 1},
        )

    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_discovery_returns_clear_error_when_required_field_missing(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        search_url = "https://example.com/search?q=三体&page=1"
        stub_httpx_request(
            monkeypatch,
            {
                search_url: build_response(
                    "GET",
                    search_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div class="result-item">
                        <span class="author">刘慈欣</span>
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source["id"], "keyword": "三体", "page": 1},
        )

    assert response.status_code == 400
    assert "title" in response.json()["detail"].lower()


def test_discovery_returns_clear_error_for_timeout(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        search_url = "https://example.com/search?q=三体&page=1"
        stub_httpx_request(
            monkeypatch,
            {
                search_url: httpx.TimeoutException("request timeout"),
            },
        )

        response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source["id"], "keyword": "三体", "page": 1},
        )

    assert response.status_code == 400
    assert "timeout" in response.json()["detail"].lower()


def test_discovery_returns_clear_error_for_invalid_runtime_url(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        response = client.post(
            "/api/online-discovery/detail",
            json={"source_id": source["id"], "detail_url": "ftp://example.com/book/1"},
        )

    assert response.status_code == 400
    assert "http/https" in response.json()["detail"].lower()


def test_discovery_returns_clear_error_for_response_type_mismatch(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        detail_url = "https://example.com/books/1"
        stub_httpx_request(
            monkeypatch,
            {
                detail_url: build_response(
                    "GET",
                    detail_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="<html><body>not json</body></html>",
                ),
            },
        )

        response = client.post(
            "/api/online-discovery/detail",
            json={"source_id": source["id"], "detail_url": detail_url},
        )

    assert response.status_code == 400
    assert "response type" in response.json()["detail"].lower()
