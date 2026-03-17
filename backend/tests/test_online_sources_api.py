from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application


VALID_DEFINITION = {
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
                "attr": "href",
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
        },
    },
    "detail": {
        "request": {
            "method": "GET",
            "url": "{{detail_url}}",
            "response_type": "html",
        },
        "fields": {
            "title": {
                "parser": "css",
                "expr": "h1.book-title",
                "required": True,
            },
            "author": {
                "parser": "css",
                "expr": ".book-author",
            },
            "description": {
                "parser": "css",
                "expr": ".book-intro",
            },
            "cover_url": {
                "parser": "css",
                "expr": ".book-cover img",
                "attr": "src",
            },
            "catalog_url": {
                "parser": "css",
                "expr": "a.catalog-link",
                "attr": "href",
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
            "parser": "css",
            "expr": ".chapter-item",
        },
        "fields": {
            "chapter_title": {
                "parser": "css",
                "expr": "a",
                "required": True,
            },
            "chapter_url": {
                "parser": "css",
                "expr": "a",
                "attr": "href",
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
                "parser": "css",
                "expr": "#content",
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


def build_source_payload(**overrides):
    payload = {
        "name": "起点公开站点",
        "description": "Phase 1 合法书源定义",
        "enabled": True,
        "base_url": "https://example.com",
        "definition": VALID_DEFINITION,
    }
    payload.update(overrides)
    return payload


def test_online_source_endpoints_require_authentication(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    with TestClient(create_application()) as client:
        response = client.get("/api/online-sources")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_and_get_online_source(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post("/api/online-sources", json=build_source_payload())
        assert create_response.status_code == 201
        payload = create_response.json()

        detail_response = client.get(f"/api/online-sources/{payload['id']}")

    assert payload["name"] == "起点公开站点"
    assert payload["enabled"] is True
    assert payload["base_url"] == "https://example.com"
    assert payload["validation_status"] == "valid"
    assert payload["validation_errors"] == []
    assert payload["definition"]["search"]["request"]["method"] == "GET"
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == payload["id"]


def test_list_online_sources_returns_created_items(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        first_response = client.post(
            "/api/online-sources",
            json=build_source_payload(name="书源 A"),
        )
        second_response = client.post(
            "/api/online-sources",
            json=build_source_payload(name="书源 B", base_url="https://books.example.com"),
        )
        assert first_response.status_code == 201
        assert second_response.status_code == 201

        list_response = client.get("/api/online-sources")

    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == ["书源 B", "书源 A"]


def test_update_online_source_revalidates_definition(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post("/api/online-sources", json=build_source_payload())
        source_id = create_response.json()["id"]

        update_response = client.put(
            f"/api/online-sources/{source_id}",
            json=build_source_payload(
                name="更新后的书源",
                description="更新后的描述",
                enabled=False,
                base_url="https://reader.example.com/",
            ),
        )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["name"] == "更新后的书源"
    assert payload["description"] == "更新后的描述"
    assert payload["enabled"] is False
    assert payload["base_url"] == "https://reader.example.com"
    assert payload["validation_status"] == "valid"


def test_delete_online_source_removes_it(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post("/api/online-sources", json=build_source_payload())
        source_id = create_response.json()["id"]

        delete_response = client.delete(f"/api/online-sources/{source_id}")
        list_response = client.get("/api/online-sources")

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_validate_online_source_rejects_authorization_header(monkeypatch, tmp_path):
    invalid_definition = {
        **VALID_DEFINITION,
        "detail": {
            **VALID_DEFINITION["detail"],
            "request": {
                **VALID_DEFINITION["detail"]["request"],
                "headers": {
                    "Authorization": "Bearer secret-token",
                },
            },
        },
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/validate",
            json={
                "base_url": "https://example.com",
                "definition": invalid_definition,
            },
        )

    assert response.status_code == 400
    assert "Authorization" in response.json()["detail"]


def test_validate_online_source_rejects_unknown_placeholder(monkeypatch, tmp_path):
    invalid_definition = {
        **VALID_DEFINITION,
        "search": {
            **VALID_DEFINITION["search"],
            "request": {
                **VALID_DEFINITION["search"]["request"],
                "url": "/search?q={{keyword}}&token={{secret_token}}",
            },
        },
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/validate",
            json={
                "base_url": "https://example.com",
                "definition": invalid_definition,
            },
        )

    assert response.status_code == 400
    assert "secret_token" in response.json()["detail"]


def test_validate_online_source_accepts_phase1_definition(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/validate",
            json={
                "base_url": "https://example.com/",
                "definition": VALID_DEFINITION,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    assert payload["errors"] == []
    assert payload["normalized_base_url"] == "https://example.com"
    assert payload["normalized_definition"]["catalog"]["request"]["method"] == "GET"
