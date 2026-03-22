from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_runtime_error_mapping import DetectorRuntimeErrorMappingResult
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorRuntimeFacingGateOutcome(str, Enum):
    NO_GATE_CANDIDATE = "no_gate_candidate"
    GATE_CANDIDATE_CARRIED = "gate_candidate_carried"


class DetectorRuntimeFacingGateDecision(str, Enum):
    GATE_DECISION_NOOP = "gate_decision_noop"


class DetectorRuntimeFacingGateCandidateKind(str, Enum):
    NONE = "none"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GATEWAY_CANDIDATE = "gateway_candidate"


class DetectorRuntimeFacingGateCandidate(ORMModel):
    """Internal-only runtime-facing gate candidate near future external error behavior."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    kind: DetectorRuntimeFacingGateCandidateKind
    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_candidate_shape(self):
        if self.kind == DetectorRuntimeFacingGateCandidateKind.NONE:
            raise ValueError("runtime-facing gate candidate kind must not be none")
        if self.kind == DetectorRuntimeFacingGateCandidateKind.CHALLENGE_CANDIDATE:
            if self.category != DetectorCategory.CHALLENGE_CANDIDATE:
                raise ValueError("challenge gate candidate kind must match challenge detector category")
            if self.recommended_error_code != LegadoRuntimeCode.ANTI_BOT_CHALLENGE:
                raise ValueError("challenge gate candidate must keep challenge recommended_error_code")
        if self.kind == DetectorRuntimeFacingGateCandidateKind.GATEWAY_CANDIDATE:
            if self.category != DetectorCategory.GATEWAY_CANDIDATE:
                raise ValueError("gateway gate candidate kind must match gateway detector category")
            if self.recommended_error_code != LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY:
                raise ValueError("gateway gate candidate must keep gateway recommended_error_code")
        return self


class DetectorRuntimeFacingGateInput(ORMModel):
    """Internal-only input contract for future runtime-facing error gate work."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    runtime_error_mapping_result: DetectorRuntimeErrorMappingResult
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None
    gate_candidate_kind: DetectorRuntimeFacingGateCandidateKind = DetectorRuntimeFacingGateCandidateKind.NONE

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        mapping_input = self.runtime_error_mapping_result.mapping_input
        if self.stage != mapping_input.stage:
            raise ValueError("runtime-facing gate input stage must match runtime error mapping input stage")
        if self.expected_response_type != mapping_input.expected_response_type:
            raise ValueError(
                "runtime-facing gate input expected_response_type must match runtime error mapping input expected_response_type"
            )
        if self.detector_result != mapping_input.detector_result:
            raise ValueError(
                "runtime-facing gate input detector_result must match runtime error mapping input detector_result"
            )
        if self.recommended_error_code != mapping_input.recommended_error_code:
            raise ValueError(
                "runtime-facing gate input recommended_error_code must match runtime error mapping input recommended_error_code"
            )

        expected_kind = DetectorRuntimeFacingGateCandidateKind.NONE
        mapping_candidate = self.runtime_error_mapping_result.mapping_candidate
        if mapping_candidate is not None:
            if mapping_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
                expected_kind = DetectorRuntimeFacingGateCandidateKind.CHALLENGE_CANDIDATE
            elif mapping_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
                expected_kind = DetectorRuntimeFacingGateCandidateKind.GATEWAY_CANDIDATE
            else:
                raise ValueError("runtime-facing gate input only supports challenge/gateway mapping candidates")

        if self.gate_candidate_kind != expected_kind:
            raise ValueError("runtime-facing gate input gate_candidate_kind must match runtime error mapping result")
        return self


class DetectorRuntimeFacingGateResult(ORMModel):
    """Internal-only no-op runtime-facing gate result."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorRuntimeFacingGateOutcome
    gate_decision: DetectorRuntimeFacingGateDecision
    gate_input: DetectorRuntimeFacingGateInput
    gate_candidate: DetectorRuntimeFacingGateCandidate | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorRuntimeFacingGateOutcome.NO_GATE_CANDIDATE:
            if self.gate_candidate is not None:
                raise ValueError("no_gate_candidate result must not carry gate_candidate")
            if self.gate_input.gate_candidate_kind != DetectorRuntimeFacingGateCandidateKind.NONE:
                raise ValueError("no_gate_candidate result requires gate_candidate_kind none")
            return self

        if self.gate_candidate is None:
            raise ValueError("gate_candidate_carried result requires gate_candidate")
        if self.gate_input.gate_candidate_kind == DetectorRuntimeFacingGateCandidateKind.NONE:
            raise ValueError("gate_candidate_carried result requires non-none gate_candidate_kind")
        if self.gate_candidate.kind != self.gate_input.gate_candidate_kind:
            raise ValueError("gate_candidate kind must match gate_input gate_candidate_kind")
        if self.gate_candidate.recommended_error_code != self.gate_input.recommended_error_code:
            raise ValueError("gate_candidate recommended_error_code must match gate_input recommended_error_code")
        return self
