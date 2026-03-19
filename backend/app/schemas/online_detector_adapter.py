from enum import Enum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.online_detector import DetectorClassificationResult, DetectorInput
from app.schemas.online_live_seam import FetchErrorSummary, FetchSuccessSummary


class DetectorAdapterOutcome(str, Enum):
    NOOP = "noop"
    DETECTOR_INPUT_PREPARED = "detector_input_prepared"
    DETECTOR_RESULT_ATTACHED = "detector_result_attached"


class DetectorAdapterInput(ORMModel):
    """Internal adapter input contract for future live seam wiring."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str = Field(min_length=1, max_length=32)
    expected_response_type: str = Field(min_length=1, max_length=16)
    fetch_outcome_summary: FetchSuccessSummary | FetchErrorSummary

    @model_validator(mode="after")
    def _ensure_consistent_summary(self):
        if self.stage != self.fetch_outcome_summary.stage:
            raise ValueError("adapter input stage must match fetch outcome summary stage")
        if self.expected_response_type != self.fetch_outcome_summary.expected_response_type:
            raise ValueError(
                "adapter input expected_response_type must match fetch outcome summary expected_response_type"
            )
        return self


class DetectorAdapterOutput(ORMModel):
    """Internal adapter output contract for future live seam wiring."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    outcome: DetectorAdapterOutcome
    adapter_input: DetectorAdapterInput
    detector_input: DetectorInput | None = None
    detector_result: DetectorClassificationResult | None = None

    @model_validator(mode="after")
    def _ensure_outcome_shape(self):
        if self.outcome == DetectorAdapterOutcome.NOOP:
            if self.detector_input is not None or self.detector_result is not None:
                raise ValueError("noop adapter output must not carry detector_input or detector_result")
            return self

        if self.outcome == DetectorAdapterOutcome.DETECTOR_INPUT_PREPARED:
            if self.detector_input is None:
                raise ValueError("detector_input_prepared output requires detector_input")
            if self.detector_result is not None:
                raise ValueError("detector_input_prepared output must not carry detector_result")
            return self

        if self.outcome == DetectorAdapterOutcome.DETECTOR_RESULT_ATTACHED:
            if self.detector_input is None or self.detector_result is None:
                raise ValueError(
                    "detector_result_attached output requires both detector_input and detector_result"
                )
        return self
