import json
from contextlib import contextmanager

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models.online_catalog_entry import OnlineCatalogEntry
from app.models.online_chapter_cache import OnlineChapterCache
from app.models.online_reading_progress import OnlineReadingProgress
from app.models.online_shelf_book import OnlineShelfBook


ONLINE_SOURCE_DEFINITION = {
    "search": {
        "request": {
            "method": "GET",
            "url": "/search?q={{keyword}}&page={{page}}",
            "response_type": "html",
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


def create_source(client: TestClient) -> dict:
    response = client.post(
        "/api/online-sources",
        json={
            "name": "持久化阅读书源",
            "description": "用于 online_books 测试",
            "enabled": True,
            "base_url": "https://example.com",
            "definition": ONLINE_SOURCE_DEFINITION,
        },
    )
    assert response.status_code == 201
    return response.json()


def stub_httpx_request(monkeypatch, responses_by_url: dict[str, httpx.Response | Exception]):
    call_counts: dict[str, int] = {}

    def _request(method: str, url: str, **kwargs):
        call_counts[url] = call_counts.get(url, 0) + 1
        response_or_error = responses_by_url[url]
        if isinstance(response_or_error, Exception):
            raise response_or_error
        return response_or_error

    monkeypatch.setattr(httpx, "request", _request)
    return call_counts


def build_response(method: str, url: str, *, status_code: int = 200, headers: dict[str, str] | None = None, content: bytes | str = b"") -> httpx.Response:
    request = httpx.Request(method, url)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return httpx.Response(status_code=status_code, headers=headers, content=content, request=request)


def get_admin_user_id() -> int:
    session = database.create_session()
    try:
        return int(session.execute(text("SELECT id FROM users WHERE username = 'admin'")).scalar_one())
    finally:
        session.close()


def count_model(model) -> int:
    session = database.create_session()
    try:
        return session.query(model).count()
    finally:
        session.close()


def get_only_online_book_id() -> int:
    session = database.create_session()
    try:
        return int(session.query(OnlineShelfBook).one().id)
    finally:
        session.close()


def create_added_online_book(client: TestClient, source_id: int) -> dict:
    response = client.post(
        "/api/online-books",
        json={
            "source_id": source_id,
            "detail_url": "https://example.com/books/1",
            "remote_book_id": "book-1",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_add_online_book_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
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
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
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
                        <li class="chapter-item"><a href="/books/1/ch2">第二章 夜航</a></li>
                      </ul>
                    </body></html>
                    """,
                ),
            },
        )

        response = create_added_online_book(client, source["id"])

    assert response["title"] == "三体"
    assert response["remote_book_id"] == "book-1"
    assert response["total_chapters"] == 2
    assert count_model(OnlineShelfBook) == 1
    assert count_model(OnlineCatalogEntry) == 2


def test_add_online_book_is_idempotent(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
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
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
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

        first_response = client.post(
            "/api/online-books",
            json={"source_id": source["id"], "detail_url": detail_url, "remote_book_id": "book-1"},
        )
        second_response = client.post(
            "/api/online-books",
            json={"source_id": source["id"], "detail_url": detail_url, "remote_book_id": "book-1"},
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert count_model(OnlineShelfBook) == 1


def test_get_online_book_detail_and_catalog_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
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
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
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
                        <li class="chapter-item"><a href="/books/1/ch2">第二章 夜航</a></li>
                      </ul>
                    </body></html>
                    """,
                ),
            },
        )

        created = create_added_online_book(client, source["id"])
        detail_response = client.get(f"/api/online-books/{created['id']}")
        catalog_response = client.get(f"/api/online-books/{created['id']}/catalog")

    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "三体"
    assert detail_response.json()["source_id"] == source["id"]

    assert catalog_response.status_code == 200
    assert len(catalog_response.json()) == 2
    assert catalog_response.json()[0]["chapter_index"] == 0


def test_get_online_book_chapter_success_and_cache_hit(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        detail_url = "https://example.com/books/1"
        catalog_url = "https://example.com/books/1/catalog"
        chapter_url = "https://example.com/books/1/ch1"
        call_counts = stub_httpx_request(
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
                chapter_url: build_response(
                    "GET",
                    chapter_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div id="content">第一段<br/>第二段</div>
                    </body></html>
                    """,
                ),
            },
        )

        created = create_added_online_book(client, source["id"])
        first_response = client.get(f"/api/online-books/{created['id']}/chapters/0")
        second_response = client.get(f"/api/online-books/{created['id']}/chapters/0")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert "第一段" in first_response.json()["content"]
    assert first_response.json()["content"] == second_response.json()["content"]
    assert call_counts[chapter_url] == 1
    assert count_model(OnlineChapterCache) == 1


def test_online_progress_read_and_write_success(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
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
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
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

        created = create_added_online_book(client, source["id"])
        put_response = client.put(
            f"/api/online-books/{created['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 12,
                "percent": 34.5,
                "updated_at": "2026-03-17T12:00:00+00:00",
            },
        )
        get_response = client.get(f"/api/online-books/{created['id']}/progress")

    assert put_response.status_code == 200
    assert put_response.json()["percent"] == 34.5
    assert get_response.status_code == 200
    assert get_response.json()["char_offset"] == 12
    assert count_model(OnlineReadingProgress) == 1


def test_delete_online_book_cleans_catalog_cache_and_progress(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
        detail_url = "https://example.com/books/1"
        catalog_url = "https://example.com/books/1/catalog"
        chapter_url = "https://example.com/books/1/ch1"
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
                chapter_url: build_response(
                    "GET",
                    chapter_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div id="content">第一段<br/>第二段</div>
                    </body></html>
                    """,
                ),
            },
        )

        created = create_added_online_book(client, source["id"])
        client.get(f"/api/online-books/{created['id']}/chapters/0")
        client.put(
            f"/api/online-books/{created['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 5,
                "percent": 12.0,
                "updated_at": "2026-03-17T12:30:00+00:00",
            },
        )

        delete_response = client.delete(f"/api/online-books/{created['id']}")
        detail_response = client.get(f"/api/online-books/{created['id']}")

    assert delete_response.status_code == 204
    assert detail_response.status_code == 404
    assert count_model(OnlineShelfBook) == 0
    assert count_model(OnlineCatalogEntry) == 0
    assert count_model(OnlineChapterCache) == 0
    assert count_model(OnlineReadingProgress) == 0


def test_online_book_defaults_to_default_group_and_groups_can_be_updated(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        source = create_source(client)
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
                                "title": "三体",
                                "author": "刘慈欣",
                                "description": "科幻史诗",
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

        created = create_added_online_book(client, source["id"])
        groups_response = client.get("/api/book-groups")
        default_group = next(group for group in groups_response.json() if group["name"] == "默认分组")
        extra_group_response = client.post("/api/book-groups", json={"name": "在线收藏"})
        assert extra_group_response.status_code == 201
        extra_group_id = extra_group_response.json()["id"]

        get_groups_response = client.get(f"/api/online-books/{created['id']}/groups")
        update_groups_response = client.put(
            f"/api/online-books/{created['id']}/groups",
            json={"group_ids": [default_group["id"], extra_group_id]},
        )
        detail_response = client.get(f"/api/online-books/{created['id']}")

    assert get_groups_response.status_code == 200
    assert [group["name"] for group in get_groups_response.json()] == ["默认分组"]

    assert update_groups_response.status_code == 200
    assert {group["name"] for group in update_groups_response.json()} == {"默认分组", "在线收藏"}

    assert detail_response.status_code == 200
    assert {group["name"] for group in detail_response.json()["groups"]} == {"默认分组", "在线收藏"}
