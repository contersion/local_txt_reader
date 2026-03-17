from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application


BOOK_TEXT = "\u4e09\u4f53\n\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"


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


def upload_book(client: TestClient, file_name: str = "grouped-book.txt") -> dict:
    response = client.post(
        "/api/books/upload",
        files={"file": (file_name, BOOK_TEXT.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def get_default_group(groups: list[dict]) -> dict:
    return next(group for group in groups if group["name"] == "\u9ed8\u8ba4\u5206\u7ec4")


def test_create_group_requires_unique_non_blank_name(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        blank_response = client.post("/api/book-groups", json={"name": "   "})
        first_response = client.post("/api/book-groups", json={"name": "\u79d1\u5e7b"})
        duplicate_response = client.post("/api/book-groups", json={"name": "\u79d1\u5e7b"})

    assert blank_response.status_code == 400
    assert blank_response.json()["detail"] == "Group name cannot be empty"
    assert first_response.status_code == 201
    assert first_response.json()["name"] == "\u79d1\u5e7b"
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Group name already exists"


def test_rename_group_and_list_groups(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post("/api/book-groups", json={"name": "\u5f85\u91cd\u547d\u540d"})
        group_id = create_response.json()["id"]

        rename_response = client.put(f"/api/book-groups/{group_id}", json={"name": "\u5df2\u91cd\u547d\u540d"})
        list_response = client.get("/api/book-groups")

    assert rename_response.status_code == 200
    assert rename_response.json()["name"] == "\u5df2\u91cd\u547d\u540d"
    assert list_response.status_code == 200
    assert any(group["name"] == "\u5df2\u91cd\u547d\u540d" for group in list_response.json())


def test_book_groups_can_be_updated_but_not_cleared(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client)
        groups_response = client.get("/api/book-groups")
        default_group = get_default_group(groups_response.json())
        create_group_response = client.post("/api/book-groups", json={"name": "\u6536\u85cf"})
        second_group_id = create_group_response.json()["id"]

        update_response = client.put(
            f"/api/books/{book['id']}/groups",
            json={"group_ids": [default_group["id"], second_group_id]},
        )
        current_groups_response = client.get(f"/api/books/{book['id']}/groups")
        books_response = client.get("/api/books")
        empty_response = client.put(
            f"/api/books/{book['id']}/groups",
            json={"group_ids": []},
        )

    assert update_response.status_code == 200
    assert {group["name"] for group in update_response.json()} == {"\u9ed8\u8ba4\u5206\u7ec4", "\u6536\u85cf"}
    assert current_groups_response.status_code == 200
    assert {group["name"] for group in current_groups_response.json()} == {"\u9ed8\u8ba4\u5206\u7ec4", "\u6536\u85cf"}
    assert books_response.status_code == 200
    assert {group["name"] for group in books_response.json()[0]["groups"]} == {"\u9ed8\u8ba4\u5206\u7ec4", "\u6536\u85cf"}
    assert empty_response.status_code == 400
    assert empty_response.json()["detail"] == "Book must belong to at least one group"


def test_delete_group_prevents_books_from_losing_all_groups(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client)
        groups_response = client.get("/api/book-groups")
        default_group = get_default_group(groups_response.json())

        blocked_delete_response = client.delete(f"/api/book-groups/{default_group['id']}")

        create_group_response = client.post("/api/book-groups", json={"name": "\u5907\u4efd"})
        second_group_id = create_group_response.json()["id"]
        assign_response = client.put(
            f"/api/books/{book['id']}/groups",
            json={"group_ids": [default_group["id"], second_group_id]},
        )
        delete_second_response = client.delete(f"/api/book-groups/{second_group_id}")
        final_groups_response = client.get(f"/api/books/{book['id']}/groups")

    assert blocked_delete_response.status_code == 409
    assert blocked_delete_response.json()["detail"] == "Deleting this group would leave some books without any group"
    assert assign_response.status_code == 200
    assert delete_second_response.status_code == 204
    assert final_groups_response.status_code == 200
    assert [group["name"] for group in final_groups_response.json()] == ["\u9ed8\u8ba4\u5206\u7ec4"]


def test_delete_group_prevents_online_books_from_losing_all_groups(monkeypatch, tmp_path):
    from tests.test_online_books_api import create_source, create_added_online_book, stub_httpx_request, build_response
    import json

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
        online_book = create_added_online_book(client, source["id"])
        groups_response = client.get("/api/book-groups")
        default_group = get_default_group(groups_response.json())

        blocked_delete_response = client.delete(f"/api/book-groups/{default_group['id']}")

        extra_group_response = client.post("/api/book-groups", json={"name": "在线备份"})
        assert extra_group_response.status_code == 201
        extra_group_id = extra_group_response.json()["id"]
        assign_response = client.put(
            f"/api/online-books/{online_book['id']}/groups",
            json={"group_ids": [default_group["id"], extra_group_id]},
        )
        delete_extra_response = client.delete(f"/api/book-groups/{extra_group_id}")
        final_groups_response = client.get(f"/api/online-books/{online_book['id']}/groups")

    assert blocked_delete_response.status_code == 409
    assert blocked_delete_response.json()["detail"] == "Deleting this group would leave some books without any group"
    assert assign_response.status_code == 200
    assert delete_extra_response.status_code == 204
    assert final_groups_response.status_code == 200
    assert [group["name"] for group in final_groups_response.json()] == ["默认分组"]

