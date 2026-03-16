from typing import Literal

from pydantic import Field

from app.schemas.common import ORMModel


BookSortPreference = Literal["created_at", "recent_read", "title"]
ReaderThemePreference = Literal["light", "dark"]


class BookshelfPreferences(ORMModel):
    sort: BookSortPreference = "created_at"
    search: str = Field(default="", max_length=200)
    group_id: int | None = Field(default=None, ge=1)
    page: int = Field(default=1, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=100)


class ReaderPreferences(ORMModel):
    font_size: int = Field(default=19, ge=15, le=32)
    line_height: float = Field(default=1.95, ge=1.45, le=2.6)
    letter_spacing: float = Field(default=0.0, ge=0.0, le=2.0)
    paragraph_spacing: float = Field(default=1.0, ge=0.0, le=2.5)
    content_width: int = Field(default=72, ge=56, le=96)
    theme: ReaderThemePreference = "light"


class UserPreferencesDocument(ORMModel):
    version: int = 1
    bookshelf: BookshelfPreferences = Field(default_factory=BookshelfPreferences)
    reader: ReaderPreferences = Field(default_factory=ReaderPreferences)


class BookshelfPreferencesPatch(ORMModel):
    sort: BookSortPreference | None = None
    search: str | None = Field(default=None, max_length=200)
    group_id: int | None = Field(default=None, ge=1)
    page: int | None = Field(default=None, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=100)


class ReaderPreferencesPatch(ORMModel):
    font_size: int | None = Field(default=None, ge=15, le=32)
    line_height: float | None = Field(default=None, ge=1.45, le=2.6)
    letter_spacing: float | None = Field(default=None, ge=0.0, le=2.0)
    paragraph_spacing: float | None = Field(default=None, ge=0.0, le=2.5)
    content_width: int | None = Field(default=None, ge=56, le=96)
    theme: ReaderThemePreference | None = None


class UserPreferencesPatchRequest(ORMModel):
    bookshelf: BookshelfPreferencesPatch | None = None
    reader: ReaderPreferencesPatch | None = None


class UserPreferencesResponse(ORMModel):
    has_saved_preferences: bool
    preferences: UserPreferencesDocument
