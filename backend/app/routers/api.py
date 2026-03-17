from fastapi import APIRouter

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.book_groups import router as book_groups_router
from app.routers.books import router as books_router
from app.routers.chapter_rules import router as chapter_rules_router
from app.routers.health import router as health_router
from app.routers.library import router as library_router
from app.routers.online_books import router as online_books_router
from app.routers.online_discovery import router as online_discovery_router
from app.routers.online_source_import import router as online_source_import_router
from app.routers.online_sources import router as online_sources_router
from app.routers.preferences import router as preferences_router


api_router = APIRouter()
api_v1_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chapter_rules_router)
api_router.include_router(book_groups_router)
api_router.include_router(books_router)
api_router.include_router(library_router)
api_router.include_router(online_books_router)
api_router.include_router(online_discovery_router)
api_router.include_router(online_source_import_router)
api_router.include_router(online_sources_router)
api_router.include_router(preferences_router)
api_router.include_router(api_v1_router)

