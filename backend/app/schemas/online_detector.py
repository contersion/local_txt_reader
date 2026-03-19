from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorCategory(str, Enum):
    NO_MATCH = "no_match"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GATEWAY_CANDIDATE = "gateway_candidate"


class DetectorMatchStatus(str, Enum):
    NO_MATCH = "no_match"
    CANDIDATE_MATCH = "candidate_match"
    DEFERRED = "deferred"


class DetectorDeferredRequirementHint(str, Enum):
    NONE = "none"
    JS_RUNTIME = "js_runtime"
    BROWSER_RUNTIME = "browser_runtime"
    MANUAL_REVIEW = "manual_review"


class DetectorInput(ORMModel):
    """Normalized, bounded detector input for the offline Phase 3-B.7 skeleton."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: Literal["search", "detail", "catalog", "content"]
    expected_response_type: Literal["html", "json"]
    requested_url: str = Field(min_length=1, max_length=2000)
    final_url: str = Field(min_length=1, max_length=2000)
    status_code: int = Field(ge=100, le=599)
    content_type: str = Field(min_length=1, max_length=255)
    redirected: bool
    body_text_preview: str = Field(default="", max_length=4096)
    body_text_length: int = Field(ge=0)


class DetectorClassificationResult(ORMModel):
    """Structured detector result for offline candidate classification only."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    category: DetectorCategory
    status: DetectorMatchStatus
    matched_signals: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    recommended_error_code: LegadoRuntimeCode | None = None
    deferred_requirement_hint: DetectorDeferredRequirementHint = DetectorDeferredRequirementHint.NONE
