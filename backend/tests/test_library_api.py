import json
from contextlib import contextmanager
from datetime import datetime, timezone

import httpx
from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models.book import Book
from app.models.online_shelf_book import OnlineShelfBook


ONLINE_SOURCE_DEFINITION = {
    "search": {
        "request": {
            "method": "GET",
            "url": "/search?q={{keyword}}&page={{page}}",
            "response_type": "html",
        },
        "list_selector": {"parser": "css", "expr": ".result-item"},
        "fields": {
            "remote_book_id": {"parser": "css", "expr": "a.title", "attr": "data-book-id", "required": True},
            "title": {"parser": "css", "expr": "a.title", "required": True},
            "detail_url": {"parser": "css", "expr": "a.title", "attr": "href", "required": True},
        },
    },
    "detail": {
        "request": {"method": "GET", "url": "{{detail_url}}", "response_type": "json"},
        "fields": {
            "title": {"parser": "jsonpath", "expr": "$.book.title", "required": True},
            "author": {"parser": "jsonpath", "expr": "$.book.author"},
            "description": {"parser": "jsonpath", "expr": "$.book.description"},
            "cover_url": {"parser": "jsonpath", "expr": "$.book.cover"},
            "catalog_url": {"parser": "jsonpath", "expr": "$.book.catalog_url", "required": True},
        },
    },
    "catalog": {
        "request": {"method": "GET", "url": "{{catalog_url}}", "response_type": "html"},
        "list_selector": {"parser": "xpath", "expr": "//li[@class='chapter-item']"},
        "fields": {
            "chapter_title": {"parser": "xpath", "expr": "./a/text()", "required": True},
            "chapter_url": {"parser": "xpath", "expr": "./a/@href", "required": True},
        },
    },
    "content": {
        "request": {"method": "GET", "url": "{{chapter_url}}", "response_type": "html"},
        "fields": {
            "content": {"parser": "regex", "expr": "<div id=\"content\">([\\s\\S]+?)</div>", "regex_group": 1, "required": True},
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
        login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        access_token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        yield client


def upload_local_book(client: TestClient, file_name: str, text: str, *, author: str | None = None) -> dict:
    response = client.post(
        "/api/books/upload",
        files={"file": (file_name, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    book = response.json()
    if author:
        update_response = client.patch(
            f"/api/books/{book['id']}",
            json={"author": author},
        )
        assert update_response.status_code == 200
        book = update_response.json()
    return book


def create_online_source(client: TestClient) -> dict:
    response = client.post(
        "/api/online-sources",
        json={
            "name": "聚合测试书源",
            "description": "用于 library 聚合测试",
            "enabled": True,
            "base_url": "https://example.com",
            "definition": ONLINE_SOURCE_DEFINITION,
        },
    )
    assert response.status_code == 201
    return response.json()


def add_online_book(client: TestClient, source_id: int, *, detail_url: str, remote_book_id: str) -> dict:
    response = client.post(
        "/api/online-books",
        json={
            "source_id": source_id,
            "detail_url": detail_url,
            "remote_book_id": remote_book_id,
        },
    )
    assert response.status_code == 200
    return response.json()


def stub_httpx_request(monkeypatch, responses_by_url: dict[str, httpx.Response | Exception]):
    def _request(method: str, url: str, **kwargs):
        response_or_error = responses_by_url[url]
        if isinstance(response_or_error, Exception):
            raise response_or_error
        return response_or_error

    monkeypatch.setattr(httpx, "request", _request)


def build_response(method: str, url: str, *, headers: dict[str, str] | None = None, content: bytes | str = b"") -> httpx.Response:
    request = httpx.Request(method, url)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return httpx.Response(200, headers=headers, content=content, request=request)


def prepare_online_book_stubs(monkeypatch):
    detail_url = "https://example.com/books/1"
    catalog_url = "https://example.com/books/1/catalog"
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
                            "title": "银河边缘",
                            "author": "在线作者",
                            "description": "在线图书简介",
                            "cover": "https://example.com/covers/1.jpg",
                            "catalog_url": catalog_url,
                        }
                    }
                ),
            ),
            catalog_url: build_response(
                "GET",
                catalog_url,
                headers={"content-type": "text/html; charset=utf-8"},
                content="""
                <html><body>
                  <ul>
                    <li class="chapter-item"><a href="/books/1/ch1">第一章 开始</a></li>
                  </ul>
                </body></html>
                """,
            ),
        },
    )
    return detail_url


def set_local_book_created_at(book_id: int, value: datetime) -> None:
    session = database.create_session()
    try:
        book = session.query(Book).filter(Book.id == book_id).one()
        book.created_at = value
        session.commit()
    finally:
        session.close()


def set_online_book_created_at(online_book_id: int, value: datetime) -> None:
    session = database.create_session()
    try:
        book = session.query(OnlineShelfBook).filter(OnlineShelfBook.id == online_book_id).one()
        book.created_at = value
        session.commit()
    finally:
        session.close()


def test_library_books_requires_authentication(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    with TestClient(create_application()) as client:
        response = client.get("/api/library/books")

    assert response.status_code == 401


def test_library_books_returns_local_and_online_items(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        local_book = upload_local_book(client, "local-alpha.txt", "第1章 开始\n正文", author="本地作者")
        detail_url = prepare_online_book_stubs(monkeypatch)
        source = create_online_source(client)
        online_book = add_online_book(client, source["id"], detail_url=detail_url, remote_book_id="book-1")

        response = client.get("/api/library/books")

    assert response.status_code == 200
    payload = response.json()
    assert {item["library_id"] for item in payload} == {f"local:{local_book['id']}", f"online:{online_book['id']}"}
    local_item = next(item for item in payload if item["source_kind"] == "local")
    online_item = next(item for item in payload if item["source_kind"] == "online")
    assert local_item["groups"] != []
    assert online_item["groups"] != []


def test_library_books_supports_source_filter_search_and_library_id(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        local_book = upload_local_book(client, "deep-space.txt", "第1章 开始\n正文", author="刘慈欣")
        detail_url = prepare_online_book_stubs(monkeypatch)
        source = create_online_source(client)
        online_book = add_online_book(client, source["id"], detail_url=detail_url, remote_book_id="book-1")

        local_only = client.get("/api/library/books", params={"source_kind": "local"})
        online_only = client.get("/api/library/books", params={"source_kind": "online"})
        search_local = client.get("/api/library/books", params={"q": "deep"})
        search_online = client.get("/api/library/books", params={"q": "在线作者"})

    assert local_only.status_code == 200
    assert [item["library_id"] for item in local_only.json()] == [f"local:{local_book['id']}"]

    assert online_only.status_code == 200
    assert [item["library_id"] for item in online_only.json()] == [f"online:{online_book['id']}"]

    assert [item["library_id"] for item in search_local.json()] == [f"local:{local_book['id']}"]
    assert [item["library_id"] for item in search_online.json()] == [f"online:{online_book['id']}"]


def test_library_books_supports_sorting(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        local_book = upload_local_book(client, "zulu.txt", "第1章 开始\n正文", author="本地作者")
        detail_url = prepare_online_book_stubs(monkeypatch)
        source = create_online_source(client)
        online_book = add_online_book(client, source["id"], detail_url=detail_url, remote_book_id="book-1")

        set_local_book_created_at(local_book["id"], datetime(2026, 3, 15, 8, 0, tzinfo=timezone.utc))
        set_online_book_created_at(online_book["id"], datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc))

        client.put(
            f"/api/books/{local_book['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 3,
                "percent": 10.0,
                "updated_at": "2026-03-15T09:00:00+00:00",
            },
        )
        client.put(
            f"/api/online-books/{online_book['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 4,
                "percent": 50.0,
                "updated_at": "2026-03-16T09:00:00+00:00",
            },
        )

        created_response = client.get("/api/library/books", params={"sort_by": "created_at", "sort_order": "desc"})
        recent_response = client.get("/api/library/books", params={"sort_by": "recent_read_at", "sort_order": "desc"})
        title_response = client.get("/api/library/books", params={"sort_by": "title", "sort_order": "asc"})

    assert [item["source_kind"] for item in created_response.json()] == ["online", "local"]
    assert [item["source_kind"] for item in recent_response.json()] == ["online", "local"]
    assert [item["title"] for item in title_response.json()] == ["银河边缘", "zulu"]
