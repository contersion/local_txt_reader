from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector_gate import DetectorGateResult
from app.schemas.online_detector_runtime_visible_gate import (
    DetectorRuntimeVisibleGateDecision,
    DetectorRuntimeVisibleGateInput,
    DetectorRuntimeVisibleGateOutcome,
    DetectorRuntimeVisibleGateResult,
    DetectorRuntimeVisibleGateSignal,
)


def prepare_detector_runtime_visible_gate_input(
    gate_result: DetectorGateResult | Mapping[str, Any],
) -> DetectorRuntimeVisibleGateInput:
    normalized_gate_result = _coerce_gate_result(gate_result)
    gate_input = normalized_gate_result.gate_input
    return DetectorRuntimeVisibleGateInput.model_validate(
        {
            "stage": gate_input.stage,
            "expected_response_type": gate_input.expected_response_type,
            "gate_result": normalized_gate_result,
            "adapter_output": gate_input.adapter_output,
            "detector_result": gate_input.detector_result,
            "recommended_error_code": gate_input.recommended_error_code,
        }
    )


def build_detector_runtime_visible_gate_result(
    visible_gate_input: DetectorRuntimeVisibleGateInput | Mapping[str, Any],
) -> DetectorRuntimeVisibleGateResult:
    normalized_input = _coerce_visible_gate_input(visible_gate_input)
    runtime_visible_signal = _build_runtime_visible_signal(normalized_input.gate_result)
    outcome = (
        DetectorRuntimeVisibleGateOutcome.VISIBLE_SIGNAL_CARRIED
        if runtime_visible_signal is not None
        else DetectorRuntimeVisibleGateOutcome.NO_VISIBLE_SIGNAL
    )
    return DetectorRuntimeVisibleGateResult.model_validate(
        {
            "outcome": outcome,
            "visible_gate_decision": DetectorRuntimeVisibleGateDecision.VISIBLE_GATE_DECISION_NOOP,
            "visible_gate_input": normalized_input,
            "runtime_visible_signal": runtime_visible_signal,
        }
    )


def evaluate_detector_runtime_visible_gate_noop(
    gate_result_or_visible_input: DetectorGateResult | DetectorRuntimeVisibleGateInput | Mapping[str, Any],
) -> DetectorRuntimeVisibleGateResult:
    if isinstance(gate_result_or_visible_input, DetectorRuntimeVisibleGateInput):
        return build_detector_runtime_visible_gate_result(gate_result_or_visible_input)
    visible_input = prepare_detector_runtime_visible_gate_input(gate_result_or_visible_input)
    return build_detector_runtime_visible_gate_result(visible_input)


def _build_runtime_visible_signal(gate_result: DetectorGateResult) -> DetectorRuntimeVisibleGateSignal | None:
    if gate_result.carried_signal is None:
        return None
    return DetectorRuntimeVisibleGateSignal.model_validate(
        {
            "category": gate_result.carried_signal.category,
            "status": gate_result.carried_signal.status,
            "recommended_error_code": gate_result.carried_signal.recommended_error_code,
        }
    )


def _coerce_gate_result(gate_result: DetectorGateResult | Mapping[str, Any]) -> DetectorGateResult:
    if isinstance(gate_result, httpx.Response) or isinstance(gate_result, BaseException):
        raise TypeError("runtime-visible gating skeleton only accepts gate results or mapping-like stubs")
    if isinstance(gate_result, DetectorGateResult):
        return gate_result
    if not isinstance(gate_result, Mapping):
        raise TypeError("runtime-visible gating skeleton only accepts mapping-like stubs")
    return DetectorGateResult.model_validate(dict(gate_result))


def _coerce_visible_gate_input(
    visible_gate_input: DetectorRuntimeVisibleGateInput | Mapping[str, Any],
) -> DetectorRuntimeVisibleGateInput:
    if isinstance(visible_gate_input, httpx.Response) or isinstance(visible_gate_input, BaseException):
        raise TypeError("runtime-visible gating skeleton only accepts visible gate inputs or mapping-like stubs")
    if isinstance(visible_gate_input, DetectorRuntimeVisibleGateInput):
        return visible_gate_input
    if not isinstance(visible_gate_input, Mapping):
        raise TypeError("runtime-visible gating skeleton only accepts mapping-like stubs")
    return DetectorRuntimeVisibleGateInput.model_validate(dict(visible_gate_input))
