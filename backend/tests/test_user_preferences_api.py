from contextlib import contextmanager
import sqlite3

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.core import database
from app.core.config import settings
from app.main import create_application


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


def test_get_preferences_returns_defaults_when_user_has_no_saved_preferences(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/preferences")

    assert response.status_code == 200
    payload = response.json()
    assert payload["has_saved_preferences"] is False
    assert payload["preferences"] == {
        "version": 1,
        "bookshelf": {
            "sort": "created_at",
            "search": "",
            "group_id": None,
            "page": 1,
            "page_size": None,
        },
        "reader": {
            "font_size": 19,
            "line_height": 1.95,
            "letter_spacing": 0.0,
            "paragraph_spacing": 1.0,
            "content_width": 72,
            "theme": "light",
        },
    }


def test_patch_preferences_persists_bookshelf_and_reader_settings(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        patch_response = client.patch(
            "/api/preferences",
            json={
                "bookshelf": {
                    "sort": "title",
                    "search": "三体",
                    "group_id": 3,
                    "page": 2,
                    "page_size": 24,
                },
                "reader": {
                    "font_size": 21,
                    "line_height": 2.15,
                    "letter_spacing": 0.8,
                    "paragraph_spacing": 1.4,
                    "content_width": 76,
                    "theme": "dark",
                },
            },
        )
        get_response = client.get("/api/preferences")

    assert patch_response.status_code == 200
    patch_payload = patch_response.json()
    assert patch_payload["has_saved_preferences"] is True
    assert patch_payload["preferences"]["bookshelf"] == {
        "sort": "title",
        "search": "三体",
        "group_id": 3,
        "page": 2,
        "page_size": 24,
    }
    assert patch_payload["preferences"]["reader"] == {
        "font_size": 21,
        "line_height": 2.15,
        "letter_spacing": 0.8,
        "paragraph_spacing": 1.4,
        "content_width": 76,
        "theme": "dark",
    }
    assert get_response.status_code == 200
    assert get_response.json() == patch_payload


def test_get_preferences_normalizes_invalid_legacy_payload(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE users
                    SET preferences_json = :payload
                    WHERE username = 'admin'
                    """
                ),
                {
                    "payload": (
                        '{"version":"legacy","bookshelf":{"sort":"invalid","search":123,"group_id":-1,'
                        '"page":0,"page_size":-5},"reader":{"font_size":999,"line_height":0.2,'
                        '"letter_spacing":-4,"paragraph_spacing":"bad","content_width":10,"theme":"sepia"}}'
                    )
                },
            )

        response = client.get("/api/preferences")

    assert response.status_code == 200
    payload = response.json()
    assert payload["has_saved_preferences"] is True
    assert payload["preferences"] == {
        "version": 1,
        "bookshelf": {
            "sort": "created_at",
            "search": "",
            "group_id": None,
            "page": 1,
            "page_size": None,
        },
        "reader": {
            "font_size": 19,
            "line_height": 1.95,
            "letter_spacing": 0.0,
            "paragraph_spacing": 1.0,
            "content_width": 72,
            "theme": "light",
        },
    }


def test_init_db_backfills_preferences_column_for_existing_users_table(monkeypatch, tmp_path):
    db_path = tmp_path / "legacy.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    from app.init_data import create_database_schema

    create_database_schema()

    inspector = inspect(database.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    assert "preferences_json" in columns
