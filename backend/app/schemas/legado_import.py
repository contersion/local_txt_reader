from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel
from app.schemas.online_source import OnlineSourceDefinition


class LegadoImportCode(str, Enum):
    UNSUPPORTED_JS = "LEGADO_UNSUPPORTED_JS"
    UNSUPPORTED_COOKIE = "LEGADO_UNSUPPORTED_COOKIE"
    UNSUPPORTED_AUTHORIZATION = "LEGADO_UNSUPPORTED_AUTHORIZATION"
    UNSUPPORTED_LOGIN_STATE = "LEGADO_UNSUPPORTED_LOGIN_STATE"
    UNSUPPORTED_WEBVIEW = "LEGADO_UNSUPPORTED_WEBVIEW"
    UNSUPPORTED_PROXY = "LEGADO_UNSUPPORTED_PROXY"
    UNSUPPORTED_DYNAMIC_VARIABLE = "LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE"
    UNSUPPORTED_CONDITION_DSL = "LEGADO_UNSUPPORTED_CONDITION_DSL"
    UNSUPPORTED_CHARSET_OVERRIDE = "LEGADO_UNSUPPORTED_CHARSET_OVERRIDE"
    UNSUPPORTED_REPLACE_DSL = "LEGADO_UNSUPPORTED_REPLACE_DSL"
    UNSUPPORTED_PARSER = "LEGADO_UNSUPPORTED_PARSER"
    UNSUPPORTED_METHOD = "LEGADO_UNSUPPORTED_METHOD"
    UNSUPPORTED_PLACEHOLDER = "LEGADO_UNSUPPORTED_PLACEHOLDER"
    UNSUPPORTED_MULTI_REQUEST = "LEGADO_UNSUPPORTED_MULTI_REQUEST"
    UNSUPPORTED_DYNAMIC_REQUEST = "LEGADO_UNSUPPORTED_DYNAMIC_REQUEST"
    UNSUPPORTED_FIELD = "LEGADO_UNSUPPORTED_FIELD"
    INVALID_URL = "LEGADO_INVALID_URL"
    REQUIRED_FIELD_MISSING = "LEGADO_REQUIRED_FIELD_MISSING"
    MAPPING_FAILED = "LEGADO_MAPPING_FAILED"
    IGNORED_FIELD = "LEGADO_IGNORED_FIELD"
    CSS_HTML_NORMALIZED = "LEGADO_CSS_HTML_NORMALIZED"


class LegadoIssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class LegadoImportIssue(ORMModel):
    code: LegadoImportCode
    error_code: LegadoImportCode
    message: str
    field: str | None = None
    severity: LegadoIssueSeverity
    source_path: str | None = None
    stage: str | None = None
    field_name: str | None = None
    raw_value: Any | None = None
    normalized_value: Any | None = None


class LegadoImportRequest(ORMModel):
    model_config = ConfigDict(extra="forbid")

    source: dict[str, Any] = Field(default_factory=dict)


class LegadoMappedSource(ORMModel):
    name: str
    description: str | None = None
    enabled: bool
    base_url: str
    definition: OnlineSourceDefinition


class LegadoImportResult(ORMModel):
    is_valid: bool
    mapped_source: LegadoMappedSource | None = None
    source_id: int | None = None
    errors: list[LegadoImportIssue] = Field(default_factory=list)
    warnings: list[LegadoImportIssue] = Field(default_factory=list)
    ignored_fields: list[str] = Field(default_factory=list)
    unsupported_fields: list[str] = Field(default_factory=list)
