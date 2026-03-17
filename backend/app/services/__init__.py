from app.services.auth import authenticate_user, get_user_by_username
from app.services.book_chapters import replace_book_chapters, save_book_chapters
from app.services.books import (
    BookAccessError,
    BookChapterNotFoundError,
    BookDeleteError,
    BookNotFoundError,
    BookReadError,
    BookReparseError,
    BookUploadError,
    create_uploaded_book,
    delete_user_book,
    get_user_book,
    get_user_book_chapter,
    get_user_book_detail,
    list_user_book_chapters,
    list_user_books,
    read_book_chapter_content,
    read_book_text,
    reparse_user_book,
)
from app.services.chapter_rules import BUILTIN_RULES
from app.services.chapter_splitter import ChapterSegment, split_book_into_chapters
from app.services.library import list_library_books
from app.services.reading_progress import get_user_reading_progress, upsert_user_reading_progress

__all__ = [
    "authenticate_user",
    "get_user_by_username",
    "get_user_book",
    "get_user_book_detail",
    "list_user_books",
    "list_user_book_chapters",
    "get_user_book_chapter",
    "read_book_text",
    "read_book_chapter_content",
    "create_uploaded_book",
    "delete_user_book",
    "reparse_user_book",
    "get_user_reading_progress",
    "upsert_user_reading_progress",
    "save_book_chapters",
    "replace_book_chapters",
    "split_book_into_chapters",
    "ChapterSegment",
    "list_library_books",
    "BookAccessError",
    "BookNotFoundError",
    "BookChapterNotFoundError",
    "BookReadError",
    "BookUploadError",
    "BookDeleteError",
    "BookReparseError",
    "BUILTIN_RULES",
]
