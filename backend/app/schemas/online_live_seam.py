from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel


class FetchOutcomeKind(str, Enum):
    SUCCESS = "success"
    HTTP_ERROR = "http_error"
    TRANSPORT_ERROR = "transport_error"


class FetchExceptionKind(str, Enum):
    TIMEOUT = "timeout"
    INVALID_URL = "invalid_url"
    REQUEST_ERROR = "request_error"
    OTHER = "other"


class FetchOutcomeSummaryBase(ORMModel):
    """Internal-only summary contract for future live seam wiring."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: Literal["search", "detail", "catalog", "content"]
    expected_response_type: Literal["html", "json"]
    requested_url: str = Field(min_length=1, max_length=2000)
    fetch_outcome_kind: FetchOutcomeKind
    final_url: str | None = Field(default=None, min_length=1, max_length=2000)
    status_code: int | None = Field(default=None, ge=100, le=599)
    content_type: str | None = Field(default=None, min_length=1, max_length=255)
    redirected: bool | None = None
    body_text_preview: str | None = Field(default=None, max_length=4096)
    body_text_length: int | None = Field(default=None, ge=0)
    exception_kind: FetchExceptionKind | None = None


class FetchSuccessSummary(FetchOutcomeSummaryBase):
    """Success-path summary for future live seam skeleton work."""

    fetch_outcome_kind: Literal[FetchOutcomeKind.SUCCESS]

    @model_validator(mode="after")
    def _ensure_success_only_shape(self):
        if self.exception_kind is not None:
            raise ValueError("success summary must not carry exception_kind")
        return self


class FetchErrorSummary(FetchOutcomeSummaryBase):
    """Error-path summary for future live seam skeleton work."""

    fetch_outcome_kind: Literal[FetchOutcomeKind.HTTP_ERROR, FetchOutcomeKind.TRANSPORT_ERROR]

    @model_validator(mode="after")
    def _ensure_error_shape(self):
        if self.fetch_outcome_kind == FetchOutcomeKind.HTTP_ERROR and self.status_code is None:
            raise ValueError("http_error summary requires status_code")
        if self.fetch_outcome_kind == FetchOutcomeKind.TRANSPORT_ERROR and self.exception_kind is None:
            raise ValueError("transport_error summary requires exception_kind")
        return self
