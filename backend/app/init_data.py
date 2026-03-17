from collections.abc import Callable
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - ensure model modules are imported before create_all
from app.core import database
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User
from app.services.auth import get_user_by_username
from app.services.book_groups import ensure_all_user_book_groups
from app.services.chapter_rules import seed_builtin_rules
from app.utils.files import ensure_directory


Seeder = Callable[[Session], None]


def ensure_runtime_directories() -> dict[str, Path]:
    directories = {
        "data_dir": ensure_directory(settings.data_dir),
        "upload_dir": ensure_directory(settings.upload_dir),
        "cover_dir": ensure_directory(settings.upload_dir / "covers"),
    }

    database_path = database.engine.url.database
    if database_path:
        ensure_directory(Path(database_path).expanduser().resolve().parent)

    return directories


def create_database_schema() -> None:
    database.Base.metadata.create_all(bind=database.engine)
    _apply_sqlite_compat_migrations()


def verify_database_connection() -> None:
    with database.engine.begin() as connection:
        connection.execute(text("SELECT 1"))


def run_seeders() -> None:
    seeders: tuple[Seeder, ...] = (
        _seed_default_user,
        _seed_builtin_chapter_rules,
        _seed_book_groups,
    )
    with database.session_scope() as session:
        for seeder in seeders:
            seeder(session)
        session.commit()


def init_db() -> None:
    ensure_runtime_directories()
    create_database_schema()
    verify_database_connection()
    run_seeders()


def _seed_default_user(session: Session) -> None:
    existing_user = get_user_by_username(session, settings.default_admin_username)
    if existing_user is None:
        session.add(
            User(
                username=settings.default_admin_username,
                password_hash=get_password_hash(settings.default_admin_password),
            )
        )
        session.flush()


def _seed_builtin_chapter_rules(session: Session) -> None:
    seed_builtin_rules(session)


def _seed_book_groups(session: Session) -> None:
    ensure_all_user_book_groups(session)


def bootstrap_application() -> None:
    init_db()


def _apply_sqlite_compat_migrations() -> None:
    inspector = inspect(database.engine)
    table_names = set(inspector.get_table_names())
    if "books" not in table_names and "users" not in table_names and "online_shelf_books" not in table_names:
        return

    statements: list[str] = []

    if "books" in table_names:
        book_columns = {column["name"] for column in inspector.get_columns("books")}
        if "cover_path" not in book_columns:
            statements.append("ALTER TABLE books ADD COLUMN cover_path VARCHAR(500)")

    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "preferences_json" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN preferences_json TEXT")

    if not statements:
        return

    with database.engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
