from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_detector import DetectorCategory
from app.schemas.online_detector_runtime_facing_behavior_gate import DetectorRuntimeFacingBehaviorGateResult
from app.schemas.online_detector_runtime_facing_behavior_activation import (
    DetectorRuntimeFacingBehaviorActivationCandidate,
    DetectorRuntimeFacingBehaviorActivationCandidateKind,
    DetectorRuntimeFacingBehaviorActivationDecision,
    DetectorRuntimeFacingBehaviorActivationInput,
    DetectorRuntimeFacingBehaviorActivationOutcome,
    DetectorRuntimeFacingBehaviorActivationResult,
)


def prepare_detector_runtime_facing_behavior_activation_input(
    runtime_facing_behavior_gate_result: DetectorRuntimeFacingBehaviorGateResult | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorActivationInput:
    normalized_behavior_gate_result = _coerce_runtime_facing_behavior_gate_result(
        runtime_facing_behavior_gate_result
    )
    behavior_gate_input = normalized_behavior_gate_result.behavior_gate_input
    return DetectorRuntimeFacingBehaviorActivationInput.model_validate(
        {
            "stage": behavior_gate_input.stage,
            "expected_response_type": behavior_gate_input.expected_response_type,
            "runtime_facing_behavior_gate_result": normalized_behavior_gate_result,
            "detector_result": behavior_gate_input.detector_result,
            "recommended_error_code": behavior_gate_input.recommended_error_code,
            "activation_candidate_kind": _infer_activation_candidate_kind(normalized_behavior_gate_result),
        }
    )


def build_detector_runtime_facing_behavior_activation_result(
    activation_input: DetectorRuntimeFacingBehaviorActivationInput | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorActivationResult:
    normalized_input = _coerce_activation_input(activation_input)
    activation_candidate = _build_activation_candidate(normalized_input.runtime_facing_behavior_gate_result)
    outcome = (
        DetectorRuntimeFacingBehaviorActivationOutcome.ACTIVATION_CANDIDATE_CARRIED
        if activation_candidate is not None
        else DetectorRuntimeFacingBehaviorActivationOutcome.NO_ACTIVATION_CANDIDATE
    )
    return DetectorRuntimeFacingBehaviorActivationResult.model_validate(
        {
            "outcome": outcome,
            "activation_decision": DetectorRuntimeFacingBehaviorActivationDecision.ACTIVATION_DECISION_NOOP,
            "activation_input": normalized_input,
            "activation_candidate": activation_candidate,
        }
    )


def evaluate_detector_runtime_facing_behavior_activation_noop(
    runtime_facing_behavior_gate_result_or_activation_input: DetectorRuntimeFacingBehaviorActivationInput
    | DetectorRuntimeFacingBehaviorGateResult
    | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorActivationResult:
    if isinstance(
        runtime_facing_behavior_gate_result_or_activation_input,
        DetectorRuntimeFacingBehaviorActivationInput,
    ):
        return build_detector_runtime_facing_behavior_activation_result(
            runtime_facing_behavior_gate_result_or_activation_input
        )
    activation_input = prepare_detector_runtime_facing_behavior_activation_input(
        runtime_facing_behavior_gate_result_or_activation_input
    )
    return build_detector_runtime_facing_behavior_activation_result(activation_input)


def _build_activation_candidate(
    runtime_facing_behavior_gate_result: DetectorRuntimeFacingBehaviorGateResult,
) -> DetectorRuntimeFacingBehaviorActivationCandidate | None:
    behavior_gate_candidate = runtime_facing_behavior_gate_result.behavior_gate_candidate
    if behavior_gate_candidate is None:
        return None
    return DetectorRuntimeFacingBehaviorActivationCandidate.model_validate(
        {
            "kind": _infer_activation_candidate_kind(runtime_facing_behavior_gate_result),
            "category": behavior_gate_candidate.category,
            "status": behavior_gate_candidate.status,
            "recommended_error_code": behavior_gate_candidate.recommended_error_code,
        }
    )


def _infer_activation_candidate_kind(
    runtime_facing_behavior_gate_result: DetectorRuntimeFacingBehaviorGateResult,
) -> DetectorRuntimeFacingBehaviorActivationCandidateKind:
    behavior_gate_candidate = runtime_facing_behavior_gate_result.behavior_gate_candidate
    if behavior_gate_candidate is None:
        return DetectorRuntimeFacingBehaviorActivationCandidateKind.NONE
    if behavior_gate_candidate.category == DetectorCategory.CHALLENGE_CANDIDATE:
        return DetectorRuntimeFacingBehaviorActivationCandidateKind.CHALLENGE_CANDIDATE
    if behavior_gate_candidate.category == DetectorCategory.GATEWAY_CANDIDATE:
        return DetectorRuntimeFacingBehaviorActivationCandidateKind.GATEWAY_CANDIDATE
    raise ValueError(
        "runtime-facing behavior activation skeleton only supports challenge/gateway behavior gate candidates"
    )


def _coerce_runtime_facing_behavior_gate_result(
    runtime_facing_behavior_gate_result: DetectorRuntimeFacingBehaviorGateResult | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorGateResult:
    if isinstance(runtime_facing_behavior_gate_result, httpx.Response) or isinstance(
        runtime_facing_behavior_gate_result, BaseException
    ):
        raise TypeError(
            "runtime-facing behavior activation skeleton only accepts runtime-facing behavior gate results or mapping-like stubs"
        )
    if isinstance(runtime_facing_behavior_gate_result, DetectorRuntimeFacingBehaviorGateResult):
        return runtime_facing_behavior_gate_result
    if not isinstance(runtime_facing_behavior_gate_result, Mapping):
        raise TypeError("runtime-facing behavior activation skeleton only accepts mapping-like stubs")
    return DetectorRuntimeFacingBehaviorGateResult.model_validate(dict(runtime_facing_behavior_gate_result))


def _coerce_activation_input(
    activation_input: DetectorRuntimeFacingBehaviorActivationInput | Mapping[str, Any],
) -> DetectorRuntimeFacingBehaviorActivationInput:
    if isinstance(activation_input, httpx.Response) or isinstance(activation_input, BaseException):
        raise TypeError(
            "runtime-facing behavior activation skeleton only accepts activation inputs or mapping-like stubs"
        )
    if isinstance(activation_input, DetectorRuntimeFacingBehaviorActivationInput):
        return activation_input
    if not isinstance(activation_input, Mapping):
        raise TypeError("runtime-facing behavior activation skeleton only accepts mapping-like stubs")
    return DetectorRuntimeFacingBehaviorActivationInput.model_validate(dict(activation_input))
