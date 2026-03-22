from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector import DetectorCategory
from app.schemas.online_detector_runtime_facing_gate import DetectorRuntimeFacingGateResult
from app.schemas.online_detector_runtime_facing_behavior_gate import (
    DetectorRuntimeFacingBehaviorGateCandidate,
    DetectorRuntimeFacingBehaviorGateCandidateKind,
    DetectorRuntimeFacingBehaviorGateDecision,
    DetectorRuntimeFacingBehaviorGateInput,
    DetectorRuntimeFacingBehaviorGateOutcome,
    DetectorRuntimeFacingBehaviorGateResult,
)


def prepare_detector_runtime_facing_behavior_gate_input(
    runtime_facing_gate_result: DetectorRuntimeFacingGateResult | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorGateInput:
    normalized_gate_result = _coerce_runtime_facing_gate_result(runtime_facing_gate_result)
    gate_input = normalized_gate_result.gate_input
    return DetectorRuntimeFacingBehaviorGateInput.model_validate(
        {
            "stage": gate_input.stage,
            "expected_response_type": gate_input.expected_response_type,
            "runtime_facing_error_gate_result": normalized_gate_result,
            "detector_result": gate_input.detector_result,
            "recommended_error_code": gate_input.recommended_error_code,
            "behavior_gate_candidate_kind": _infer_behavior_gate_candidate_kind(normalized_gate_result),
        }
    )


def build_detector_runtime_facing_behavior_gate_result(
    behavior_gate_input: DetectorRuntimeFacingBehaviorGateInput | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorGateResult:
    normalized_input = _coerce_behavior_gate_input(behavior_gate_input)
    behavior_gate_candidate = _build_behavior_gate_candidate(normalized_input.runtime_facing_error_gate_result)
    outcome = (
        DetectorRuntimeFacingBehaviorGateOutcome.BEHAVIOR_GATE_CANDIDATE_CARRIED
        if behavior_gate_candidate is not None
        else DetectorRuntimeFacingBehaviorGateOutcome.NO_BEHAVIOR_GATE_CANDIDATE
    )
    return DetectorRuntimeFacingBehaviorGateResult.model_validate(
        {
            "outcome": outcome,
            "behavior_gate_decision": DetectorRuntimeFacingBehaviorGateDecision.BEHAVIOR_GATE_DECISION_NOOP,
            "behavior_gate_input": normalized_input,
            "behavior_gate_candidate": behavior_gate_candidate,
        }
    )


def evaluate_detector_runtime_facing_behavior_gate_noop(
    runtime_facing_gate_result_or_behavior_gate_input: DetectorRuntimeFacingBehaviorGateInput
    | DetectorRuntimeFacingGateResult
    | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorGateResult:
    if isinstance(runtime_facing_gate_result_or_behavior_gate_input, DetectorRuntimeFacingBehaviorGateInput):
        return build_detector_runtime_facing_behavior_gate_result(runtime_facing_gate_result_or_behavior_gate_input)
    behavior_gate_input = prepare_detector_runtime_facing_behavior_gate_input(
        runtime_facing_gate_result_or_behavior_gate_input
    )
    return build_detector_runtime_facing_behavior_gate_result(behavior_gate_input)


def _build_behavior_gate_candidate(
    runtime_facing_gate_result: DetectorRuntimeFacingGateResult,
) -> DetectorRuntimeFacingBehaviorGateCandidate | None:
    gate_candidate = runtime_facing_gate_result.gate_candidate
    if gate_candidate is None:
        return None
    return DetectorRuntimeFacingBehaviorGateCandidate.model_validate(
        {
            "kind": _infer_behavior_gate_candidate_kind(runtime_facing_gate_result),
            "category": gate_candidate.category,
            "status": gate_candidate.status,
            "recommended_error_code": gate_candidate.recommended_error_code,
        }
    )


def _infer_behavior_gate_candidate_kind(
    runtime_facing_gate_result: DetectorRuntimeFacingGateResult,
) -> DetectorRuntimeFacingBehaviorGateCandidateKind:
    gate_candidate = runtime_facing_gate_result.gate_candidate
    if gate_candidate is None:
        return DetectorRuntimeFacingBehaviorGateCandidateKind.NONE
    if gate_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
        return DetectorRuntimeFacingBehaviorGateCandidateKind.CHALLENGE_CANDIDATE
    if gate_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
        return DetectorRuntimeFacingBehaviorGateCandidateKind.GATEWAY_CANDIDATE
    raise ValueError("runtime-facing behavior gate skeleton only supports challenge/gateway gate candidates")


def _coerce_runtime_facing_gate_result(
    runtime_facing_gate_result: DetectorRuntimeFacingGateResult | Mapping[str, Any],
) -> DetectorRuntimeFacingGateResult:
    if isinstance(runtime_facing_gate_result, httpx.Response) or isinstance(runtime_facing_gate_result, BaseException):
        raise TypeError(
            "runtime-facing behavior gate skeleton only accepts runtime-facing gate results or mapping-like stubs"
        )
    if isinstance(runtime_facing_gate_result, DetectorRuntimeFacingGateResult):
        return runtime_facing_gate_result
    if not isinstance(runtime_facing_gate_result, Mapping):
        raise TypeError("runtime-facing behavior gate skeleton only accepts mapping-like stubs")
    return DetectorRuntimeFacingGateResult.model_validate(dict(runtime_facing_gate_result))


def _coerce_behavior_gate_input(
    behavior_gate_input: DetectorRuntimeFacingBehaviorGateInput | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorGateInput:
    if isinstance(behavior_gate_input, httpx.Response) or isinstance(behavior_gate_input, BaseException):
        raise TypeError("runtime-facing behavior gate skeleton only accepts behavior gate inputs or mapping-like stubs")
    if isinstance(behavior_gate_input, DetectorRuntimeFacingBehaviorGateInput):
        return behavior_gate_input
    if not isinstance(behavior_gate_input, Mapping):
        raise TypeError("runtime-facing behavior gate skeleton only accepts mapping-like stubs")
    return DetectorRuntimeFacingBehaviorGateInput.model_validate(dict(behavior_gate_input))
