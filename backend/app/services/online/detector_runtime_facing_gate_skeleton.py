from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector import DetectorCategory
from app.schemas.online_detector_runtime_error_mapping import DetectorRuntimeErrorMappingResult
from app.schemas.online_detector_runtime_facing_gate import (
    DetectorRuntimeFacingGateCandidate,
    DetectorRuntimeFacingGateCandidateKind,
    DetectorRuntimeFacingGateDecision,
    DetectorRuntimeFacingGateInput,
    DetectorRuntimeFacingGateOutcome,
    DetectorRuntimeFacingGateResult,
)


def prepare_detector_runtime_facing_gate_input(
    runtime_error_mapping_result: DetectorRuntimeErrorMappingResult | Mapping[str, Any],
) -> DetectorRuntimeFacingGateInput:
    normalized_mapping_result = _coerce_runtime_error_mapping_result(runtime_error_mapping_result)
    mapping_input = normalized_mapping_result.mapping_input
    return DetectorRuntimeFacingGateInput.model_validate(
        {
            "stage": mapping_input.stage,
            "expected_response_type": mapping_input.expected_response_type,
            "runtime_error_mapping_result": normalized_mapping_result,
            "detector_result": mapping_input.detector_result,
            "recommended_error_code": mapping_input.recommended_error_code,
            "gate_candidate_kind": _infer_gate_candidate_kind(normalized_mapping_result),
        }
    )


def build_detector_runtime_facing_gate_result(
    gate_input: DetectorRuntimeFacingGateInput | Mapping[str, Any],
) -> DetectorRuntimeFacingGateResult:
    normalized_input = _coerce_gate_input(gate_input)
    gate_candidate = _build_gate_candidate(normalized_input.runtime_error_mapping_result)
    outcome = (
        DetectorRuntimeFacingGateOutcome.GATE_CANDIDATE_CARRIED
        if gate_candidate is not None
        else DetectorRuntimeFacingGateOutcome.NO_GATE_CANDIDATE
    )
    return DetectorRuntimeFacingGateResult.model_validate(
        {
            "outcome": outcome,
            "gate_decision": DetectorRuntimeFacingGateDecision.GATE_DECISION_NOOP,
            "gate_input": normalized_input,
            "gate_candidate": gate_candidate,
        }
    )


def evaluate_detector_runtime_facing_gate_noop(
    runtime_error_mapping_result_or_gate_input: DetectorRuntimeFacingGateInput | DetectorRuntimeErrorMappingResult | Mapping[str, Any],
) -> DetectorRuntimeFacingGateResult:
    if isinstance(runtime_error_mapping_result_or_gate_input, DetectorRuntimeFacingGateInput):
        return build_detector_runtime_facing_gate_result(runtime_error_mapping_result_or_gate_input)
    gate_input = prepare_detector_runtime_facing_gate_input(runtime_error_mapping_result_or_gate_input)
    return build_detector_runtime_facing_gate_result(gate_input)


def _build_gate_candidate(
    runtime_error_mapping_result: DetectorRuntimeErrorMappingResult,
) -> DetectorRuntimeFacingGateCandidate | None:
    mapping_candidate = runtime_error_mapping_result.mapping_candidate
    if mapping_candidate is None:
        return None
    return DetectorRuntimeFacingGateCandidate.model_validate(
        {
            "kind": _infer_gate_candidate_kind(runtime_error_mapping_result),
            "category": mapping_candidate.category,
            "status": mapping_candidate.status,
            "recommended_error_code": mapping_candidate.recommended_error_code,
        }
    )


def _infer_gate_candidate_kind(
    runtime_error_mapping_result: DetectorRuntimeErrorMappingResult,
) -> DetectorRuntimeFacingGateCandidateKind:
    mapping_candidate = runtime_error_mapping_result.mapping_candidate
    if mapping_candidate is None:
        return DetectorRuntimeFacingGateCandidateKind.NONE
    if mapping_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
        return DetectorRuntimeFacingGateCandidateKind.CHALLENGE_CANDIDATE
    if mapping_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
        return DetectorRuntimeFacingGateCandidateKind.GATEWAY_CANDIDATE
    raise ValueError("runtime-facing gate skeleton only supports challenge/gateway mapping candidates")


def _coerce_runtime_error_mapping_result(
    runtime_error_mapping_result: DetectorRuntimeErrorMappingResult | Mapping[str, Any],
) -> DetectorRuntimeErrorMappingResult:
    if isinstance(runtime_error_mapping_result, httpx.Response) or isinstance(runtime_error_mapping_result, BaseException):
        raise TypeError("runtime-facing gate skeleton only accepts runtime error mapping results or mapping-like stubs")
    if isinstance(runtime_error_mapping_result, DetectorRuntimeErrorMappingResult):
        return runtime_error_mapping_result
    if not isinstance(runtime_error_mapping_result, Mapping):
        raise TypeError("runtime-facing gate skeleton only accepts mapping-like stubs")
    return DetectorRuntimeErrorMappingResult.model_validate(dict(runtime_error_mapping_result))


def _coerce_gate_input(
    gate_input: DetectorRuntimeFacingGateInput | Mapping[str, Any],
) -> DetectorRuntimeFacingGateInput:
    if isinstance(gate_input, httpx.Response) or isinstance(gate_input, BaseException):
        raise TypeError("runtime-facing gate skeleton only accepts gate inputs or mapping-like stubs")
    if isinstance(gate_input, DetectorRuntimeFacingGateInput):
        return gate_input
    if not isinstance(gate_input, Mapping):
        raise TypeError("runtime-facing gate skeleton only accepts mapping-like stubs")
    return DetectorRuntimeFacingGateInput.model_validate(dict(gate_input))
