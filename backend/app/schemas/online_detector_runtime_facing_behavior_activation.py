from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_runtime_facing_behavior_gate import DetectorRuntimeFacingBehaviorGateResult
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorRuntimeFacingBehaviorActivationOutcome(str, Enum):
    NO_ACTIVATION_CANDIDATE = "no_activation_candidate"
    ACTIVATION_CANDIDATE_CARRIED = "activation_candidate_carried"


class DetectorRuntimeFacingBehaviorActivationDecision(str, Enum):
    ACTIVATION_DECISION_NOOP = "activation_decision_noop"


class DetectorRuntimeFacingBehaviorActivationCandidateKind(str, Enum):
    NONE = "none"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GATEWAY_CANDIDATE = "gateway_candidate"


class DetectorRuntimeFacingBehaviorActivationCandidate(ORMModel):
    """Internal-only activation candidate near future external behavior activation boundary."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    kind: DetectorRuntimeFacingBehaviorActivationCandidateKind
    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_candidate_shape(self):
        if self.kind == DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE:
            raise ValueError("runtime-facing behavior activation candidate kind must not be none")
        if self.kind == DetectorRuntimeFacingBehaviorActivationCandidateKind.CHALLENGE_CANDIDATE:
            if self.category != DetectorCategory.CHALLENGE_CANDIDATE:
                raise ValueError(
                    "challenge activation candidate kind must match challenge detector category"
                )
            if self.recommended_error_code != LegadoRuntimeCode.ANTI_BOT_CHALLENGE:
                raise ValueError(
                    "challenge activation candidate must keep challenge recommended_error_code"
                )
        if self.kind == DetectorRuntimeFacingBehaviorActivationCandidateKind.GATEWAY_CANDIDATE:
            if self.category != DetectorCategory.GATEWAY_CANDIDATE:
                raise ValueError("gateway activation candidate kind must match gateway detector category")
            if self.recommended_error_code != LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY:
                raise ValueError("gateway activation candidate must keep gateway recommended_error_code")
        return self


class DetectorRuntimeFacingBehaviorActivationInput(ORMModel):
    """Internal-only input contract for future runtime-facing behavior activation work."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    runtime_facing_behavior_gate_result: DetectorRuntimeFacingBehaviorGateResult
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None
    activation_candidate_kind: DetectorRuntimeFacingBehaviorActivationCandidateKind = (
        DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE
    )

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        behavior_gate_input = self.runtime_facing_behavior_gate_result.behavior_gate_input
        if self.stage != behavior_gate_input.stage:
            raise ValueError(
                "runtime-facing behavior activation input stage must match runtime-facing behavior gate input stage"
            )
        if self.expected_response_type != behavior_gate_input.expected_response_type:
            raise ValueError(
                "runtime-facing behavior activation input expected_response_type must match runtime-facing behavior gate input expected_response_type"
            )
        if self.detector_result != behavior_gate_input.detector_result:
            raise ValueError(
                "runtime-facing behavior activation input detector_result must match runtime-facing behavior gate input detector_result"
            )
        if self.recommended_error_code != behavior_gate_input.recommended_error_code:
            raise ValueError(
                "runtime-facing behavior activation input recommended_error_code must match runtime-facing behavior gate input recommended_error_code"
            )

        expected_kind = DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE
        behavior_gate_candidate = self.runtime_facing_behavior_gate_result.behavior_gate_candidate
        if behavior_gate_candidate is not None:
            if behavior_gate_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
                expected_kind = DetectorRuntimeFacingBehaviorActivationCandidateKind.CHALLENGE_CANDIDATE
            elif behavior_gate_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
                expected_kind = DetectorRuntimeFacingBehaviorActivationCandidateKind.GATEWAY_CANDIDATE
            else:
                raise ValueError(
                    "runtime-facing behavior activation input only supports challenge/gateway behavior gate candidates"
                )

        if self.activation_candidate_kind != expected_kind:
            raise ValueError(
                "runtime-facing behavior activation input activation_candidate_kind must match runtime-facing behavior gate result"
            )
        return self


class DetectorRuntimeFacingBehaviorActivationResult(ORMModel):
    """Internal-only no-op runtime-facing behavior activation result."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorRuntimeFacingBehaviorActivationOutcome
    activation_decision: DetectorRuntimeFacingBehaviorActivationDecision
    activation_input: DetectorRuntimeFacingBehaviorActivationInput
    activation_candidate: DetectorRuntimeFacingBehaviorActivationCandidate | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorRuntimeFacingBehaviorActivationOutcome.NO_ACTIVATION_CANDIDATE:
            if self.activation_candidate is not None:
                raise ValueError("no_activation_candidate result must not carry activation_candidate")
            if self.activation_input.activation_candidate_kind != DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE:
                raise ValueError("no_activation_candidate result requires activation_candidate_kind none")
            return self

        if self.activation_candidate is None:
            raise ValueError("activation_candidate_carried result requires activation_candidate")
        if self.activation_input.activation_candidate_kind == DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE:
            raise ValueError(
                "activation_candidate_carried result requires non-none activation_candidate_kind"
            )
        if self.activation_candidate.kind != self.activation_input.activation_candidate_kind:
            raise ValueError(
                "activation_candidate kind must match activation_input activation_candidate_kind"
            )
        if self.activation_candidate.recommended_error_code != self.activation_input.recommended_error_code:
            raise ValueError(
                "activation_candidate recommended_error_code must match activation_input recommended_error_code"
            )
        return self
