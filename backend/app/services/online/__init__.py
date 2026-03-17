from app.services.online.online_sources import (
    OnlineSourceError,
    OnlineSourceNotFoundError,
    create_online_source,
    delete_online_source,
    get_online_source,
    list_online_sources,
    serialize_online_source,
    update_online_source,
    validate_online_source_payload,
)
from app.services.online.online_books import (
    OnlineBookNotFoundError,
    add_online_book_to_shelf,
    delete_user_online_book,
    get_user_online_book,
    get_user_online_chapter,
    list_user_online_catalog,
    serialize_online_book,
    serialize_online_catalog_entry,
    serialize_online_chapter_content,
)
from app.services.online.online_progress import (
    OnlineReadingProgressNotFoundError,
    get_online_reading_progress,
    upsert_online_reading_progress,
)
from app.services.online.content_parse_service import ContentParseError
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse, fetch_stage_response
from app.services.online.legado_importer import import_legado_source, validate_legado_import_payload
from app.services.online.legado_mapper import map_legado_source
from app.services.online.legado_validator import validate_legado_source, validate_mapped_online_source
from app.services.online.parser_engine import ParserEngineError, extract_value, select_many
from app.services.online.source_normalizer import normalize_online_source_payload
from app.services.online.source_engine import (
    OnlineDiscoveryError,
    preview_catalog,
    preview_chapter,
    preview_detail,
    preview_search,
)
from app.services.online.source_validator import OnlineSourceValidationError, validate_phase1_source_definition

__all__ = [
    "ContentParseError",
    "FetchServiceError",
    "OnlineDiscoveryError",
    "OnlineBookNotFoundError",
    "OnlineSourceError",
    "OnlineSourceNotFoundError",
    "OnlineSourceValidationError",
    "OnlineReadingProgressNotFoundError",
    "add_online_book_to_shelf",
    "create_online_source",
    "delete_online_source",
    "delete_user_online_book",
    "extract_value",
    "fetch_stage_response",
    "get_online_source",
    "get_online_reading_progress",
    "get_user_online_book",
    "get_user_online_chapter",
    "import_legado_source",
    "list_online_sources",
    "list_user_online_catalog",
    "map_legado_source",
    "normalize_online_source_payload",
    "ParserEngineError",
    "preview_catalog",
    "preview_chapter",
    "preview_detail",
    "preview_search",
    "RawFetchResponse",
    "select_many",
    "serialize_online_book",
    "serialize_online_catalog_entry",
    "serialize_online_chapter_content",
    "serialize_online_source",
    "upsert_online_reading_progress",
    "update_online_source",
    "validate_legado_import_payload",
    "validate_legado_source",
    "validate_mapped_online_source",
    "validate_online_source_payload",
    "validate_phase1_source_definition",
]
