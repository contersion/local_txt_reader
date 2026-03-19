from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector import DetectorClassificationResult
from app.schemas.online_detector_adapter import DetectorAdapterOutput
from app.schemas.online_detector_gate import (
    DetectorGateDecision,
    DetectorGateInput,
    DetectorGateOutcome,
    DetectorGateResult,
    DetectorGateSignal,
)
from app.services.online.detector_adapter_skeleton import coerce_detector_adapter_output_contract


def prepare_detector_gate_input(
    adapter_output: DetectorAdapterOutput | Mapping[str, Any],
) -> DetectorGateInput:
    normalized_output = _coerce_adapter_output(adapter_output)
    detector_result = normalized_output.detector_result
    recommended_error_code = detector_result.recommended_error_code if detector_result is not None else None
    return DetectorGateInput.model_validate(
        {
            "stage": normalized_output.adapter_input.stage,
            "expected_response_type": normalized_output.adapter_input.expected_response_type,
            "adapter_output": normalized_output,
            "detector_result": detector_result,
            "recommended_error_code": recommended_error_code,
        }
    )


def build_detector_gate_result(
    gate_input: DetectorGateInput | Mapping[str, Any],
) -> DetectorGateResult:
    normalized_input = _coerce_gate_input(gate_input)
    carried_signal = _build_carried_signal(normalized_input.detector_result)
    outcome = DetectorGateOutcome.SIGNAL_CARRIED if carried_signal is not None else DetectorGateOutcome.NO_SIGNAL
    return DetectorGateResult.model_validate(
        {
            "outcome": outcome,
            "gate_decision": DetectorGateDecision.GATE_DECISION_NOOP,
            "gate_input": normalized_input,
            "carried_signal": carried_signal,
        }
    )


def evaluate_detector_behavior_gate_noop(
    gate_input_or_adapter_output: DetectorGateInput | DetectorAdapterOutput | Mapping[str, Any],
) -> DetectorGateResult:
    if isinstance(gate_input_or_adapter_output, DetectorGateInput):
        return build_detector_gate_result(gate_input_or_adapter_output)
    gate_input = prepare_detector_gate_input(gate_input_or_adapter_output)
    return build_detector_gate_result(gate_input)


def _build_carried_signal(detector_result: DetectorClassificationResult | None) -> DetectorGateSignal | None:
    if detector_result is None or detector_result.recommended_error_code is None:
        return None
    return DetectorGateSignal.model_validate(
        {
            "category": detector_result.category,
            "status": detector_result.status,
            "recommended_error_code": detector_result.recommended_error_code,
        }
    )


def _coerce_adapter_output(
    adapter_output: DetectorAdapterOutput | Mapping[str, Any],
) -> DetectorAdapterOutput:
    if isinstance(adapter_output, httpx.Response) or isinstance(adapter_output, BaseException):
        raise TypeError("gating skeleton only accepts adapter outputs or mapping-like stubs")
    if isinstance(adapter_output, DetectorAdapterOutput):
        return adapter_output
    if not isinstance(adapter_output, Mapping):
        raise TypeError("gating skeleton only accepts mapping-like stubs")
    return coerce_detector_adapter_output_contract(dict(adapter_output))


def _coerce_gate_input(gate_input: DetectorGateInput | Mapping[str, Any]) -> DetectorGateInput:
    if isinstance(gate_input, httpx.Response) or isinstance(gate_input, BaseException):
        raise TypeError("gating skeleton only accepts gate inputs or mapping-like stubs")
    if isinstance(gate_input, DetectorGateInput):
        return gate_input
    if not isinstance(gate_input, Mapping):
        raise TypeError("gating skeleton only accepts mapping-like stubs")
    return DetectorGateInput.model_validate(dict(gate_input))
