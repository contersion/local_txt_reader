from datetime import datetime, timezone
from threading import RLock
from typing import Protocol

from app.schemas.online_runtime import OnlineAuthConfig, SessionContext


class SessionStorage(Protocol):
    def load(self, session_id: str) -> SessionContext | None:
        ...

    def save(self, context: SessionContext) -> SessionContext:
        ...

    def delete(self, session_id: str) -> None:
        ...


class InMemorySessionStorage:
    """Process-local runtime skeleton storage for Phase 3-A.

    This keeps session state in memory only. It is intentionally not a
    production-grade persistence layer and is unsuitable for multi-process or
    multi-instance deployments.
    """

    def __init__(self):
        self._sessions: dict[str, SessionContext] = {}
        self._lock = RLock()

    def load(self, session_id: str) -> SessionContext | None:
        with self._lock:
            context = self._sessions.get(session_id)
            return context.model_copy(deep=True) if context is not None else None

    def save(self, context: SessionContext) -> SessionContext:
        with self._lock:
            stored_context = context.model_copy(deep=True)
            self._sessions[stored_context.session_id] = stored_context
            return stored_context.model_copy(deep=True)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


class SessionHandler:
    """Resolve and manage runtime session context during the skeleton stage.

    The handler intentionally exposes only minimal save/load/clear behavior.
    It does not implement login orchestration, persistence, refresh, or
    cross-instance coordination.
    """

    def __init__(self, storage: SessionStorage | None = None):
        self.storage = storage or InMemorySessionStorage()

    def save_context(self, context: SessionContext) -> SessionContext:
        return self.storage.save(context)

    def get_context(self, session_id: str) -> SessionContext | None:
        return self.storage.load(session_id)

    def resolve_context(
        self,
        auth_config: OnlineAuthConfig | None = None,
        *,
        session_id: str | None = None,
        user_id: int | None = None,
        source_id: int | None = None,
    ) -> SessionContext | None:
        resolved_session_id = session_id or (auth_config.session_id if auth_config is not None else None)
        if not resolved_session_id:
            return None
        context = self.storage.load(resolved_session_id)
        if context is None:
            return None
        if _is_expired(context):
            self.storage.delete(resolved_session_id)
            return None
        if user_id is not None and context.user_id is not None and context.user_id != user_id:
            return None
        if source_id is not None and context.source_id is not None and context.source_id != source_id:
            return None
        return context

    def clear_context(self, session_id: str) -> None:
        self.storage.delete(session_id)


session_handler = SessionHandler()


def _is_expired(context: SessionContext) -> bool:
    if context.expires_at is None:
        return False
    expires_at = context.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc)
