from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector import DetectorCategory
from app.schemas.online_detector_runtime_error_mapping import (
    DetectorRuntimeErrorMappingCandidate,
    DetectorRuntimeErrorMappingCandidateKind,
    DetectorRuntimeErrorMappingDecision,
    DetectorRuntimeErrorMappingInput,
    DetectorRuntimeErrorMappingOutcome,
    DetectorRuntimeErrorMappingResult,
)
from app.schemas.online_detector_runtime_visible_gate import DetectorRuntimeVisibleGateResult


def prepare_detector_runtime_error_mapping_input(
    visible_gate_result: DetectorRuntimeVisibleGateResult | Mapping[str, Any],
) -> DetectorRuntimeErrorMappingInput:
    normalized_visible_gate_result = _coerce_visible_gate_result(visible_gate_result)
    visible_input = normalized_visible_gate_result.visible_gate_input
    return DetectorRuntimeErrorMappingInput.model_validate(
        {
            "stage": visible_input.stage,
            "expected_response_type": visible_input.expected_response_type,
            "visible_gate_result": normalized_visible_gate_result,
            "detector_result": visible_input.detector_result,
            "recommended_error_code": visible_input.recommended_error_code,
            "mapping_candidate_kind": _infer_mapping_candidate_kind(normalized_visible_gate_result),
        }
    )


def build_detector_runtime_error_mapping_result(
    mapping_input: DetectorRuntimeErrorMappingInput | Mapping[str, Any],
) -> DetectorRuntimeErrorMappingResult:
    normalized_input = _coerce_mapping_input(mapping_input)
    mapping_candidate = _build_mapping_candidate(normalized_input.visible_gate_result)
    outcome = (
        DetectorRuntimeErrorMappingOutcome.MAPPING_CANDIDATE_CARRIED
        if mapping_candidate is not None
        else DetectorRuntimeErrorMappingOutcome.NO_MAPPING_CANDIDATE
    )
    return DetectorRuntimeErrorMappingResult.model_validate(
        {
            "outcome": outcome,
            "mapping_decision": DetectorRuntimeErrorMappingDecision.MAPPING_DECISION_NOOP,
            "mapping_input": normalized_input,
            "mapping_candidate": mapping_candidate,
        }
    )


def evaluate_detector_runtime_error_mapping_noop(
    visible_gate_result_or_mapping_input: DetectorRuntimeErrorMappingInput | DetectorRuntimeVisibleGateResult | Mapping[str, Any],
) -> DetectorRuntimeErrorMappingResult:
    if isinstance(visible_gate_result_or_mapping_input, DetectorRuntimeErrorMappingInput):
        return build_detector_runtime_error_mapping_result(visible_gate_result_or_mapping_input)
    mapping_input = prepare_detector_runtime_error_mapping_input(visible_gate_result_or_mapping_input)
    return build_detector_runtime_error_mapping_result(mapping_input)


def _build_mapping_candidate(
    visible_gate_result: DetectorRuntimeVisibleGateResult,
) -> DetectorRuntimeErrorMappingCandidate | None:
    runtime_visible_signal = visible_gate_result.runtime_visible_signal
    if runtime_visible_signal is None:
        return None
    return DetectorRuntimeErrorMappingCandidate.model_validate(
        {
            "kind": _infer_mapping_candidate_kind(visible_gate_result),
            "category": runtime_visible_signal.category,
            "status": runtime_visible_signal.status,
            "recommended_error_code": runtime_visible_signal.recommended_error_code,
        }
    )


def _infer_mapping_candidate_kind(
    visible_gate_result: DetectorRuntimeVisibleGateResult,
) -> DetectorRuntimeErrorMappingCandidateKind:
    runtime_visible_signal = visible_gate_result.runtime_visible_signal
    if runtime_visible_signal is None:
        return DetectorRuntimeErrorMappingCandidateKind.NONE
    if runtime_visible_signal.category == DetectorCategory.CHALLENGE_CANDIDATE:
        return DetectorRuntimeErrorMappingCandidateKind.CHALLENGE_CANDIDATE
    if runtime_visible_signal.category == DetectorCategory.GATEWAY_CANDIDATE:
        return DetectorRuntimeErrorMappingCandidateKind.GATEWAY_CANDIDATE
    raise ValueError("runtime error mapping skeleton only supports challenge/gateway visible signals")


def _coerce_visible_gate_result(
    visible_gate_result: DetectorRuntimeVisibleGateResult | Mapping[str, Any],
) -> DetectorRuntimeVisibleGateResult:
    if isinstance(visible_gate_result, httpx.Response) or isinstance(visible_gate_result, BaseException):
        raise TypeError("runtime error mapping skeleton only accepts visible gate results or mapping-like stubs")
    if isinstance(visible_gate_result, DetectorRuntimeVisibleGateResult):
        return visible_gate_result
    if not isinstance(visible_gate_result, Mapping):
        raise TypeError("runtime error mapping skeleton only accepts mapping-like stubs")
    return DetectorRuntimeVisibleGateResult.model_validate(dict(visible_gate_result))


def _coerce_mapping_input(
    mapping_input: DetectorRuntimeErrorMappingInput | Mapping[str, Any],
) -> DetectorRuntimeErrorMappingInput:
    if isinstance(mapping_input, httpx.Response) or isinstance(mapping_input, BaseException):
        raise TypeError("runtime error mapping skeleton only accepts mapping inputs or mapping-like stubs")
    if isinstance(mapping_input, DetectorRuntimeErrorMappingInput):
        return mapping_input
    if not isinstance(mapping_input, Mapping):
        raise TypeError("runtime error mapping skeleton only accepts mapping-like stubs")
    return DetectorRuntimeErrorMappingInput.model_validate(dict(mapping_input))
