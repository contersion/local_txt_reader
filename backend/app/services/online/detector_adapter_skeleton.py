from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector_adapter import (
    DetectorAdapterInput,
    DetectorAdapterOutput,
    DetectorAdapterOutcome,
)
from app.schemas.online_live_seam import FetchErrorSummary, FetchOutcomeKind, FetchSuccessSummary


def prepare_detector_adapter_input(
    stub: Mapping[str, Any] | FetchSuccessSummary | FetchErrorSummary,
) -> DetectorAdapterInput:
    summary = _coerce_summary(stub)
    return DetectorAdapterInput.model_validate(
        {
            "stage": summary.stage,
            "expected_response_type": summary.expected_response_type,
            "fetch_outcome_summary": summary,
        }
    )


def prepare_detector_adapter_output_noop(
    adapter_input: DetectorAdapterInput | Mapping[str, Any],
) -> DetectorAdapterOutput:
    normalized_input = _coerce_adapter_input(adapter_input)
    return DetectorAdapterOutput.model_validate(
        {
            "outcome": DetectorAdapterOutcome.NOOP,
            "adapter_input": normalized_input,
        }
    )


def coerce_detector_adapter_output_contract(
    stub: Mapping[str, Any] | DetectorAdapterOutput,
) -> DetectorAdapterOutput:
    if isinstance(stub, httpx.Response) or isinstance(stub, BaseException):
        raise TypeError("adapter skeleton helpers only accept internal stub mappings")
    if isinstance(stub, DetectorAdapterOutput):
        return stub
    if not isinstance(stub, Mapping):
        raise TypeError("adapter skeleton helpers only accept mapping-like stubs")
    return DetectorAdapterOutput.model_validate(dict(stub))


def _coerce_summary(stub: Mapping[str, Any] | FetchSuccessSummary | FetchErrorSummary) -> FetchSuccessSummary | FetchErrorSummary:
    if isinstance(stub, httpx.Response) or isinstance(stub, BaseException):
        raise TypeError("adapter skeleton helpers only accept internal seam summaries or mapping-like stubs")
    if isinstance(stub, (FetchSuccessSummary, FetchErrorSummary)):
        return stub
    if not isinstance(stub, Mapping):
        raise TypeError("adapter skeleton helpers only accept mapping-like stubs")

    payload = dict(stub)
    outcome_kind = FetchOutcomeKind(payload["fetch_outcome_kind"])
    if outcome_kind == FetchOutcomeKind.SUCCESS:
        return FetchSuccessSummary.model_validate(payload)
    return FetchErrorSummary.model_validate(payload)


def _coerce_adapter_input(adapter_input: DetectorAdapterInput | Mapping[str, Any]) -> DetectorAdapterInput:
    if isinstance(adapter_input, httpx.Response) or isinstance(adapter_input, BaseException):
        raise TypeError("adapter skeleton helpers only accept adapter input contracts or mapping-like stubs")
    if isinstance(adapter_input, DetectorAdapterInput):
        return adapter_input
    if not isinstance(adapter_input, Mapping):
        raise TypeError("adapter skeleton helpers only accept mapping-like stubs")
    return DetectorAdapterInput.model_validate(dict(adapter_input))
