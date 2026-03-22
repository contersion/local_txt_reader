from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_runtime_facing_gate import DetectorRuntimeFacingGateResult
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorRuntimeFacingBehaviorGateOutcome(str, Enum):
    NO_BEHAVIOR_GATE_CANDIDATE = "no_behavior_gate_candidate"
    BEHAVIOR_GATE_CANDIDATE_CARRIED = "behavior_gate_candidate_carried"


class DetectorRuntimeFacingBehaviorGateDecision(str, Enum):
    BEHAVIOR_GATE_DECISION_NOOP = "behavior_gate_decision_noop"


class DetectorRuntimeFacingBehaviorGateCandidateKind(str, Enum):
    NONE = "none"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GATEWAY_CANDIDATE = "gateway_candidate"


class DetectorRuntimeFacingBehaviorGateCandidate(ORMModel):
    """Internal-only behavior gate candidate near future external behavior boundary."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    kind: DetectorRuntimeFacingBehaviorGateCandidateKind
    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_candidate_shape(self):
        if self.kind == DetectorRuntimeFacingBehaviorGateCandidateKind.NONE:
            raise ValueError("runtime-facing behavior gate candidate kind must not be none")
        if self.kind == DetectorRuntimeFacingBehaviorGateCandidateKind.CHALLENGE_CANDIDATE:
            if self.category != DetectorCategory.CHALLENGE_CANDIDATE:
                raise ValueError("challenge behavior gate candidate kind must match challenge detector category")
            if self.recommended_error_code != LegadoRuntimeCode.ANTI_BOT_CHALLENGE:
                raise ValueError("challenge behavior gate candidate must keep challenge recommended_error_code")
        if self.kind == DetectorRuntimeFacingBehaviorGateCandidateKind.GATEWAY_CANDIDATE:
            if self.category != DetectorCategory.GATEWAY_CANDIDATE:
                raise ValueError("gateway behavior gate candidate kind must match gateway detector category")
            if self.recommended_error_code != LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY:
                raise ValueError("gateway behavior gate candidate must keep gateway recommended_error_code")
        return self


class DetectorRuntimeFacingBehaviorGateInput(ORMModel):
    """Internal-only input contract for future runtime-facing behavior gate work."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    runtime_facing_error_gate_result: DetectorRuntimeFacingGateResult
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None
    behavior_gate_candidate_kind: DetectorRuntimeFacingBehaviorGateCandidateKind = (
        DetectorRuntimeFacingBehaviorGateCandidateKind.NONE
    )

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        gate_input = self.runtime_facing_error_gate_result.gate_input
        if self.stage != gate_input.stage:
            raise ValueError("runtime-facing behavior gate input stage must match runtime-facing gate input stage")
        if self.expected_response_type != gate_input.expected_response_type:
            raise ValueError(
                "runtime-facing behavior gate input expected_response_type must match runtime-facing gate input expected_response_type"
            )
        if self.detector_result != gate_input.detector_result:
            raise ValueError(
                "runtime-facing behavior gate input detector_result must match runtime-facing gate input detector_result"
            )
        if self.recommended_error_code != gate_input.recommended_error_code:
            raise ValueError(
                "runtime-facing behavior gate input recommended_error_code must match runtime-facing gate input recommended_error_code"
            )

        expected_kind = DetectorRuntimeFacingBehaviorGateCandidateKind.NONE
        gate_candidate = self.runtime_facing_error_gate_result.gate_candidate
        if gate_candidate is not None:
            if gate_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
                expected_kind = DetectorRuntimeFacingBehaviorGateCandidateKind.CHALLENGE_CANDIDATE
            elif gate_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
                expected_kind = DetectorRuntimeFacingBehaviorGateCandidateKind.GATEWAY_CANDIDATE
            else:
                raise ValueError(
                    "runtime-facing behavior gate input only supports challenge/gateway gate candidates"
                )

        if self.behavior_gate_candidate_kind != expected_kind:
            raise ValueError(
                "runtime-facing behavior gate input behavior_gate_candidate_kind must match runtime-facing gate result"
            )
        return self


class DetectorRuntimeFacingBehaviorGateResult(ORMModel):
    """Internal-only no-op runtime-facing behavior gate result."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorRuntimeFacingBehaviorGateOutcome
    behavior_gate_decision: DetectorRuntimeFacingBehaviorGateDecision
    behavior_gate_input: DetectorRuntimeFacingBehaviorGateInput
    behavior_gate_candidate: DetectorRuntimeFacingBehaviorGateCandidate | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorRuntimeFacingBehaviorGateOutcome.NO_BEHAVIOR_GATE_CANDIDATE:
            if self.behavior_gate_candidate is not None:
                raise ValueError("no_behavior_gate_candidate result must not carry behavior_gate_candidate")
            if self.behavior_gate_input.behavior_gate_candidate_kind != DetectorRuntimeFacingBehaviorGateCandidateKind.NONE:
                raise ValueError("no_behavior_gate_candidate result requires behavior_gate_candidate_kind none")
            return self

        if self.behavior_gate_candidate is None:
            raise ValueError("behavior_gate_candidate_carried result requires behavior_gate_candidate")
        if self.behavior_gate_input.behavior_gate_candidate_kind == DetectorRuntimeFacingBehaviorGateCandidateKind.NONE:
            raise ValueError(
                "behavior_gate_candidate_carried result requires non-none behavior_gate_candidate_kind"
            )
        if self.behavior_gate_candidate.kind != self.behavior_gate_input.behavior_gate_candidate_kind:
            raise ValueError("behavior_gate_candidate kind must match behavior_gate_input behavior_gate_candidate_kind")
        if self.behavior_gate_candidate.recommended_error_code != self.behavior_gate_input.recommended_error_code:
            raise ValueError(
                "behavior_gate_candidate recommended_error_code must match behavior_gate_input recommended_error_code"
            )
        return self
