from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_adapter import DetectorAdapterOutput
from app.schemas.online_detector_gate import DetectorGateResult
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorRuntimeVisibleGateOutcome(str, Enum):
    NO_VISIBLE_SIGNAL = "no_visible_signal"
    VISIBLE_SIGNAL_CARRIED = "visible_signal_carried"


class DetectorRuntimeVisibleGateDecision(str, Enum):
    VISIBLE_GATE_DECISION_NOOP = "visible_gate_decision_noop"


class DetectorRuntimeVisibleGateSignal(ORMModel):
    """Internal-only higher-layer signal near future runtime-visible gating."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None


class DetectorRuntimeVisibleGateInput(ORMModel):
    """Internal-only higher-layer visible gate input contract."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    gate_result: DetectorGateResult
    adapter_output: DetectorAdapterOutput
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        gate_input = self.gate_result.gate_input
        if self.stage != gate_input.stage:
            raise ValueError("runtime-visible gate input stage must match gate_result stage")
        if self.expected_response_type != gate_input.expected_response_type:
            raise ValueError(
                "runtime-visible gate input expected_response_type must match gate_result expected_response_type"
            )
        if self.adapter_output != gate_input.adapter_output:
            raise ValueError("runtime-visible gate input adapter_output must match gate_result adapter_output")
        if self.detector_result != gate_input.detector_result:
            raise ValueError("runtime-visible gate input detector_result must match gate_result detector_result")
        if self.recommended_error_code != gate_input.recommended_error_code:
            raise ValueError(
                "runtime-visible gate input recommended_error_code must match gate_result recommended_error_code"
            )
        return self


class DetectorRuntimeVisibleGateResult(ORMModel):
    """Internal-only higher-layer visible gate result for no-op behavior."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorRuntimeVisibleGateOutcome
    visible_gate_decision: DetectorRuntimeVisibleGateDecision
    visible_gate_input: DetectorRuntimeVisibleGateInput
    runtime_visible_signal: DetectorRuntimeVisibleGateSignal | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorRuntimeVisibleGateOutcome.NO_VISIBLE_SIGNAL and self.runtime_visible_signal is not None:
            raise ValueError("no_visible_signal result must not carry runtime_visible_signal")
        if self.outcome == DetectorRuntimeVisibleGateOutcome.VISIBLE_SIGNAL_CARRIED and self.runtime_visible_signal is None:
            raise ValueError("visible_signal_carried result requires runtime_visible_signal")
        return self
