from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_adapter import DetectorAdapterOutput
from app.schemas.online_runtime import LegadoRuntimeCode


class DetectorGateOutcome(str, Enum):
    NO_SIGNAL = "no_signal"
    SIGNAL_CARRIED = "signal_carried"


class DetectorGateDecision(str, Enum):
    GATE_DECISION_NOOP = "gate_decision_noop"


class DetectorGateSignal(ORMModel):
    """Internal-only signal carried by the minimal gating skeleton."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    category: DetectorCategory
    status: DetectorMatchStatus
    recommended_error_code: LegadoRuntimeCode | None = None


class DetectorGateInput(ORMModel):
    """Internal-only gate input contract for future gating work."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    adapter_output: DetectorAdapterOutput
    detector_result: DetectorClassificationResult | None = None
    recommended_error_code: LegadoRuntimeCode | None = None

    @model_validator(mode="after")
    def _ensure_consistent_fields(self):
        if self.stage != self.adapter_output.adapter_input.stage:
            raise ValueError("gate input stage must match adapter output stage")
        if self.expected_response_type != self.adapter_output.adapter_input.expected_response_type:
            raise ValueError("gate input expected_response_type must match adapter output expected_response_type")

        if self.detector_result != self.adapter_output.detector_result:
            raise ValueError("gate input detector_result must match adapter output detector_result")

        expected_code = self.detector_result.recommended_error_code if self.detector_result is not None else None
        if self.recommended_error_code != expected_code:
            raise ValueError("gate input recommended_error_code must match detector_result recommended_error_code")
        return self


class DetectorGateResult(ORMModel):
    """Internal-only gate result for no-op behavior gating skeleton."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorGateOutcome
    gate_decision: DetectorGateDecision
    gate_input: DetectorGateInput
    carried_signal: DetectorGateSignal | None = None

    @model_validator(mode="after")
    def _ensure_result_shape(self):
        if self.outcome == DetectorGateOutcome.NO_SIGNAL and self.carried_signal is not None:
            raise ValueError("no_signal gate result must not carry a signal")
        if self.outcome == DetectorGateOutcome.SIGNAL_CARRIED and self.carried_signal is None:
            raise ValueError("signal_carried gate result requires carried_signal")
        return self
