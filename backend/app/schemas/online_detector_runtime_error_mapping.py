from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_runtime_visible_gate import DetectorRuntimeVisibleGateResult
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorRuntimeErrorMappingOutcome(str, Enum):
    NO_MAPPING_CANDIDATE = "no_mapping_candidate"
    MAPPING_CANDIDATE_CARRIED = "mapping_candidate_carried"


class DetectorRuntimeErrorMappingDecision(str, Enum):
    MAPPING_DECISION_NOOP = "mapping_decision_noop"


class DetectorRuntimeErrorMappingCandidateKind(str, Enum):
    NONE = "none"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GATEWAY_CANDIDATE = "gateway_candidate"


class DetectorRuntimeErrorMappingCandidate(ORMModel):
    """Internal-only runtime error mapping candidate near future runtime surface."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    kind: DetectorRuntimeErrorMappingCandidateKind
    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_candidate_shape(self):
        if self.kind == DetectorRuntimeErrorMappingCandidateKind.NONE:
            raise ValueError("runtime error mapping candidate kind must not be none")
        if self.kind == DetectorRuntimeErrorMappingCandidateKind.CHALLENGE_CANDIDATE:
            if self.category != DetectorCategory.CHALLENGE_CANDIDATE:
                raise ValueError("challenge mapping candidate kind must match challenge detector category")
            if self.recommended_error_code != LegadoRuntimeCode.ANTI_BOT_CHALLENGE:
                raise ValueError("challenge mapping candidate must keep challenge recommended_error_code")
        if self.kind == DetectorRuntimeErrorMappingCandidateKind.GATEWAY_CANDIDATE:
            if self.category != DetectorCategory.GATEWAY_CANDIDATE:
                raise ValueError("gateway mapping candidate kind must match gateway detector category")
            if self.recommended_error_code != LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY:
                raise ValueError("gateway mapping candidate must keep gateway recommended_error_code")
        return self


class DetectorRuntimeErrorMappingInput(ORMModel):
    """Internal-only mapping input contract for future runtime-facing error work."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    visible_gate_result: DetectorRuntimeVisibleGateResult
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None
    mapping_candidate_kind: DetectorRuntimeErrorMappingCandidateKind = DetectorRuntimeErrorMappingCandidateKind.NONE

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        visible_input = self.visible_gate_result.visible_gate_input
        if self.stage != visible_input.stage:
            raise ValueError("runtime error mapping input stage must match visible gate input stage")
        if self.expected_response_type != visible_input.expected_response_type:
            raise ValueError(
                "runtime error mapping input expected_response_type must match visible gate input expected_response_type"
            )
        if self.detector_result != visible_input.detector_result:
            raise ValueError("runtime error mapping input detector_result must match visible gate input detector_result")
        if self.recommended_error_code != visible_input.recommended_error_code:
            raise ValueError(
                "runtime error mapping input recommended_error_code must match visible gate input recommended_error_code"
            )

        expected_kind = DetectorRuntimeErrorMappingCandidateKind.NONE
        runtime_visible_signal = self.visible_gate_result.runtime_visible_signal
        if runtime_visible_signal is not None:
            if runtime_visible_signal.category == DetectorCategory.CHALLENGE_CANDIDATE:
                expected_kind = DetectorRuntimeErrorMappingCandidateKind.CHALLENGE_CANDIDATE
            elif runtime_visible_signal.category == DetectorCategory.GATEWAY_CANDIDATE:
                expected_kind = DetectorRuntimeErrorMappingCandidateKind.GATEWAY_CANDIDATE
            else:
                raise ValueError("runtime error mapping input only supports challenge/gateway visible signals")

        if self.mapping_candidate_kind != expected_kind:
            raise ValueError("runtime error mapping input mapping_candidate_kind must match visible gate result")
        return self


class DetectorRuntimeErrorMappingResult(ORMModel):
    """Internal-only no-op runtime error mapping result."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorRuntimeErrorMappingOutcome
    mapping_decision: DetectorRuntimeErrorMappingDecision
    mapping_input: DetectorRuntimeErrorMappingInput
    mapping_candidate: DetectorRuntimeErrorMappingCandidate | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorRuntimeErrorMappingOutcome.NO_MAPPING_CANDIDATE:
            if self.mapping_candidate is not None:
                raise ValueError("no_mapping_candidate result must not carry mapping_candidate")
            if self.mapping_input.mapping_candidate_kind != DetectorRuntimeErrorMappingCandidateKind.NONE:
                raise ValueError("no_mapping_candidate result requires mapping_candidate_kind none")
            return self

        if self.mapping_candidate is None:
            raise ValueError("mapping_candidate_carried result requires mapping_candidate")
        if self.mapping_input.mapping_candidate_kind == DetectorRuntimeErrorMappingCandidateKind.NONE:
            raise ValueError("mapping_candidate_carried result requires non-none mapping_candidate_kind")
        if self.mapping_candidate.kind != self.mapping_input.mapping_candidate_kind:
            raise ValueError("mapping_candidate kind must match mapping_input mapping_candidate_kind")
        if self.mapping_candidate.recommended_error_code != self.mapping_input.recommended_error_code:
            raise ValueError("mapping_candidate recommended_error_code must match mapping_input recommended_error_code")
        return self
