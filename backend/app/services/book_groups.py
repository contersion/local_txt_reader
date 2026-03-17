from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Book, BookGroup, OnlineShelfBook
from app.models.book_group_membership import book_group_memberships
from app.models.online_book_group_membership import online_book_group_memberships


DEFAULT_BOOK_GROUP_NAME = "默认分组"
RESERVED_GROUP_NAMES = {"全部"}


class BookGroupError(ValueError):
    pass


class BookGroupNotFoundError(BookGroupError):
    pass


class BookGroupDeleteConflictError(BookGroupError):
    pass


def list_groups(db: Session, user_id: int) -> list[dict[str, object]]:
    statement = (
        select(BookGroup)
        .where(BookGroup.user_id == user_id)
        .order_by(BookGroup.is_default.desc(), BookGroup.name.asc())
    )
    groups = list(db.execute(statement).scalars().all())
    return [_get_group_payload(db, group) for group in groups]


def create_group(db: Session, user_id: int, name: str) -> dict[str, object]:
    normalized_name = _normalize_group_name(name)
    _ensure_name_is_available(db, user_id, normalized_name)

    group = BookGroup(
        user_id=user_id,
        name=normalized_name,
        is_default=_get_default_group(db, user_id) is None,
    )
    db.add(group)

    try:
        db.commit()
        db.refresh(group)
    except IntegrityError as exc:
        db.rollback()
        raise BookGroupError("Failed to create group") from exc

    return _get_group_payload(db, group)


def update_group(db: Session, user_id: int, group_id: int, name: str) -> dict[str, object]:
    group = get_user_group(db, user_id, group_id)
    normalized_name = _normalize_group_name(name)
    _ensure_name_is_available(db, user_id, normalized_name, exclude_group_id=group_id)

    group.name = normalized_name

    try:
        db.commit()
        db.refresh(group)
    except IntegrityError as exc:
        db.rollback()
        raise BookGroupError("Failed to update group") from exc

    return _get_group_payload(db, group)


def delete_group(db: Session, user_id: int, group_id: int) -> None:
    group = get_user_group(db, user_id, group_id)

    if _has_books_that_only_belong_to_group(db, user_id, group.id):
        raise BookGroupDeleteConflictError("Deleting this group would leave some books without any group")

    was_default = group.is_default
    db.delete(group)
    db.flush()

    if was_default:
        _promote_replacement_default_group(db, user_id)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BookGroupError("Failed to delete group") from exc


def get_user_group(db: Session, user_id: int, group_id: int) -> BookGroup:
    statement = select(BookGroup).where(BookGroup.id == group_id, BookGroup.user_id == user_id)
    group = db.execute(statement).scalar_one_or_none()
    if group is None:
        raise BookGroupNotFoundError("Group not found")
    return group


def get_user_groups_by_ids(db: Session, user_id: int, group_ids: Sequence[int]) -> list[BookGroup]:
    unique_ids = list(dict.fromkeys(group_ids))
    if not unique_ids:
        raise BookGroupError("Book must belong to at least one group")

    statement = select(BookGroup).where(BookGroup.user_id == user_id, BookGroup.id.in_(unique_ids))
    groups = {group.id: group for group in db.execute(statement).scalars().all()}

    if len(groups) != len(unique_ids):
        raise BookGroupError("One or more groups not found")

    return [groups[group_id] for group_id in unique_ids]


def ensure_default_group(db: Session, user_id: int) -> BookGroup:
    default_group = _get_default_group(db, user_id)
    if default_group is not None:
        return default_group

    statement = select(BookGroup).where(BookGroup.user_id == user_id, BookGroup.name == DEFAULT_BOOK_GROUP_NAME)
    existing_named_default = db.execute(statement).scalar_one_or_none()
    if existing_named_default is not None:
        existing_named_default.is_default = True
        db.flush()
        return existing_named_default

    default_group = BookGroup(user_id=user_id, name=DEFAULT_BOOK_GROUP_NAME, is_default=True)
    db.add(default_group)
    db.flush()
    return default_group


def ensure_all_user_book_groups(db: Session) -> None:
    user_ids = set(db.execute(select(Book.user_id).distinct()).scalars().all())
    user_ids.update(db.execute(select(OnlineShelfBook.user_id).distinct()).scalars().all())
    for user_id in user_ids:
        _backfill_missing_book_groups(db, user_id)


def _backfill_missing_book_groups(db: Session, user_id: int) -> None:
    books = list(
        db.execute(
            select(Book)
            .options(selectinload(Book.groups))
            .where(Book.user_id == user_id)
        )
        .scalars()
        .unique()
        .all()
    )
    books_without_groups = [book for book in books if not book.groups]
    if not books_without_groups:
        return

    default_group = ensure_default_group(db, user_id)
    for book in books_without_groups:
        book.groups.append(default_group)

    online_books = list(
        db.execute(
            select(OnlineShelfBook)
            .options(selectinload(OnlineShelfBook.groups))
            .where(OnlineShelfBook.user_id == user_id)
        )
        .scalars()
        .unique()
        .all()
    )
    online_books_without_groups = [book for book in online_books if not book.groups]
    for online_book in online_books_without_groups:
        online_book.groups.append(default_group)


def _normalize_group_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise BookGroupError("Group name cannot be empty")
    if normalized_name in RESERVED_GROUP_NAMES:
        raise BookGroupError("Group name is reserved")
    return normalized_name


def _ensure_name_is_available(db: Session, user_id: int, name: str, exclude_group_id: int | None = None) -> None:
    statement = select(BookGroup).where(BookGroup.user_id == user_id, BookGroup.name == name)
    existing_group = db.execute(statement).scalar_one_or_none()
    if existing_group is None:
        return
    if exclude_group_id is not None and existing_group.id == exclude_group_id:
        return
    raise BookGroupError("Group name already exists")


def _has_books_that_only_belong_to_group(db: Session, user_id: int, group_id: int) -> bool:
    group_book_ids = select(book_group_memberships.c.book_id).where(book_group_memberships.c.group_id == group_id)
    statement = (
        select(Book.id)
        .join(book_group_memberships, book_group_memberships.c.book_id == Book.id)
        .where(Book.user_id == user_id, Book.id.in_(group_book_ids))
        .group_by(Book.id)
        .having(func.count(book_group_memberships.c.group_id) <= 1)
    )
    if db.execute(statement.limit(1)).first() is not None:
        return True

    online_group_book_ids = select(online_book_group_memberships.c.online_book_id).where(
        online_book_group_memberships.c.group_id == group_id
    )
    online_statement = (
        select(OnlineShelfBook.id)
        .join(online_book_group_memberships, online_book_group_memberships.c.online_book_id == OnlineShelfBook.id)
        .where(OnlineShelfBook.user_id == user_id, OnlineShelfBook.id.in_(online_group_book_ids))
        .group_by(OnlineShelfBook.id)
        .having(func.count(online_book_group_memberships.c.group_id) <= 1)
    )
    return db.execute(online_statement.limit(1)).first() is not None


def _promote_replacement_default_group(db: Session, user_id: int) -> None:
    if _get_default_group(db, user_id) is not None:
        return

    statement = (
        select(BookGroup)
        .where(BookGroup.user_id == user_id)
        .order_by(BookGroup.created_at.asc(), BookGroup.id.asc())
    )
    replacement_group = db.execute(statement).scalar_one_or_none()
    if replacement_group is not None:
        replacement_group.is_default = True
        db.flush()


def _get_default_group(db: Session, user_id: int) -> BookGroup | None:
    statement = select(BookGroup).where(BookGroup.user_id == user_id, BookGroup.is_default.is_(True))
    return db.execute(statement).scalar_one_or_none()


def _get_group_payload(db: Session, group: BookGroup) -> dict[str, object]:
    local_count_statement = select(func.count(book_group_memberships.c.book_id)).where(book_group_memberships.c.group_id == group.id)
    online_count_statement = select(func.count(online_book_group_memberships.c.online_book_id)).where(
        online_book_group_memberships.c.group_id == group.id
    )
    local_book_count = db.execute(local_count_statement).scalar_one()
    online_book_count = db.execute(online_count_statement).scalar_one()
    return _serialize_group(group, int(local_book_count or 0) + int(online_book_count or 0))


def _serialize_group(group: BookGroup, book_count: int) -> dict[str, object]:
    return {
        "id": group.id,
        "name": group.name,
        "book_count": book_count,
        "created_at": group.created_at,
        "updated_at": group.updated_at,
    }

