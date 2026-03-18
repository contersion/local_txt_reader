from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel


class LegadoRuntimeCode(str, Enum):
    LOGIN_FAILED = "LEGADO_LOGIN_FAILED"
    REQUEST_TIMEOUT = "LEGADO_REQUEST_TIMEOUT"
    SESSION_MISSING = "LEGADO_SESSION_MISSING"
    COOKIE_INVALID = "LEGADO_COOKIE_INVALID"
    SESSION_EXPIRED = "LEGADO_SESSION_EXPIRED"
    AUTH_REQUIRED = "LEGADO_AUTH_REQUIRED"
    AUTH_CONFIG_INVALID = "LEGADO_AUTH_CONFIG_INVALID"
    SESSION_INJECTION_FAILED = "LEGADO_SESSION_INJECTION_FAILED"
    UNSUPPORTED_ADVANCED_AUTH = "LEGADO_UNSUPPORTED_ADVANCED_AUTH"
    BROWSER_STATE_REQUIRED = "LEGADO_BROWSER_STATE_REQUIRED"
    JS_EXECUTION_REQUIRED = "LEGADO_JS_EXECUTION_REQUIRED"
    ANTI_BOT_CHALLENGE = "LEGADO_ANTI_BOT_CHALLENGE"
    RATE_LIMITED = "LEGADO_RATE_LIMITED"
    UNSUPPORTED_REQUEST_BODY_MODE = "LEGADO_UNSUPPORTED_REQUEST_BODY_MODE"
    INVALID_HEADER_TEMPLATE = "LEGADO_INVALID_HEADER_TEMPLATE"
    UNSUPPORTED_SIGNATURE_FLOW = "LEGADO_UNSUPPORTED_SIGNATURE_FLOW"


class OnlineAuthMode(str, Enum):
    NONE = "none"
    SESSION = "session"
    COOKIE = "cookie"
    TOKEN = "token"
    HEADER = "header"


class RequestBodyMode(str, Enum):
    QUERY = "query"
    FORM = "form"
    JSON = "json"
    RAW = "raw"


class SessionCookie(ORMModel):
    """Cookie snapshot stored inside the Phase 3-A runtime skeleton."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=255)
    path: str = Field(default="/", min_length=1, max_length=255)
    secure: bool = False
    http_only: bool = False
    expires_at: datetime | None = None


class SessionContext(ORMModel):
    """Process-local runtime session context.

    Current Phase 3-A.1 code only uses this structure as an internal carrier for
    optional request injection. It is not yet persisted, synchronized across
    workers, or exposed as a public API contract.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    session_id: str = Field(min_length=1, max_length=128)
    user_id: int | None = Field(default=None, ge=1)
    source_id: int | None = Field(default=None, ge=1)
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: list[SessionCookie] = Field(default_factory=list)
    authenticated_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnlineAuthConfig(ORMModel):
    """Minimal auth configuration for runtime skeleton wiring.

    Fields currently used by code:
    - ``mode``
    - ``login_required``
    - ``session_id``
    - ``token_header_name`` validation for token/header modes

    Remaining fields are reserved for later phases and must not be interpreted
    as evidence that login, refresh, or browser-auth flows are formally
    supported today.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    mode: OnlineAuthMode = OnlineAuthMode.NONE
    login_required: bool = False
    session_id: str | None = Field(default=None, max_length=128)
    login_url: str | None = Field(default=None, max_length=2000)
    credential_fields: dict[str, str] = Field(default_factory=dict)
    token_header_name: str | None = Field(default=None, max_length=128)
    token_prefix: str | None = Field(default=None, max_length=64)
    cookie_names: list[str] = Field(default_factory=list)


class HeaderTemplateSpec(ORMModel):
    """Static-only header template metadata for L2 preflight.

    Phase 3-B.2 only validates whether the structure looks acceptable.
    It does not expand, execute, or inject these headers into runtime requests.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    headers: dict[str, str | None] = Field(default_factory=dict)


class SignaturePlaceholderSpec(ORMModel):
    """Modeled-only signature placeholder metadata.

    Phase 3-B.2 recognizes the placeholder shape so it can reject flows that
    would require a real signature engine. No signature computation happens.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    tokens: list[str] = Field(default_factory=list)


class RequestRuntimeDescriptor(ORMModel):
    """Internal-only request descriptor for Phase 3-B.2 preflight.

    This descriptor is intentionally not part of any public router schema or
    importer contract. It only carries L2 request-description metadata so the
    request pipeline can classify unsupported shapes before sending a request.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    body_mode: str | RequestBodyMode | None = None
    header_template: HeaderTemplateSpec | None = None
    signature_placeholders: SignaturePlaceholderSpec | None = None


class RequestProfile(ORMModel):
    """Final request payload after optional session/auth injection."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    method: Literal["GET", "POST"]
    url: str = Field(min_length=1)
    response_type: Literal["html", "json"]
    headers: dict[str, str] = Field(default_factory=dict)
    query: dict[str, str] = Field(default_factory=dict)
    body: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
