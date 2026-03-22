import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.online_runtime import LegadoRuntimeCode, RequestProfile
from app.services.online import content_parse_service, fetch_service, response_guard_service, source_engine
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse
from app.services.online.detector_runtime_visible_gating_skeleton import evaluate_detector_runtime_visible_gate_noop
from app.services.online.detector_runtime_error_mapping_skeleton import evaluate_detector_runtime_error_mapping_noop
from app.services.online.detector_runtime_facing_gate_skeleton import evaluate_detector_runtime_facing_gate_noop
from app.services.online.detector_runtime_facing_behavior_gate_skeleton import (
    evaluate_detector_runtime_facing_behavior_gate_noop,
)
from app.services.online.detector_runtime_facing_behavior_activation_skeleton import (
    build_detector_runtime_facing_behavior_activation_result,
    evaluate_detector_runtime_facing_behavior_activation_noop,
    prepare_detector_runtime_facing_behavior_activation_input,
)
from app.schemas.online_detector_runtime_facing_behavior_activation import (
    DetectorRuntimeFacingBehaviorActivationCandidateKind,
    DetectorRuntimeFacingBehaviorActivationDecision,
    DetectorRuntimeFacingBehaviorActivationInput,
    DetectorRuntimeFacingBehaviorActivationOutcome,
    DetectorRuntimeFacingBehaviorActivationResult,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_facing_behavior_activation_samples.json"
RUNTIME_FACING_BEHAVIOR_GATE_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "online_detector_runtime_facing_behavior_gate_samples.json"
)
RUNTIME_FACING_GATE_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_facing_gate_samples.json"
RUNTIME_ERROR_MAPPING_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_error_mapping_samples.json"
RUNTIME_VISIBLE_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_visible_gating_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_runtime_facing_behavior_gate_samples():
    return json.loads(RUNTIME_FACING_BEHAVIOR_GATE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_runtime_facing_gate_samples():
    return json.loads(RUNTIME_FACING_GATE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_runtime_error_mapping_samples():
    return json.loads(RUNTIME_ERROR_MAPPING_FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_runtime_visible_samples():
    return json.loads(RUNTIME_VISIBLE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_visible_gate_result(sample_id: str):
    runtime_visible_sample = next(
        sample for sample in _load_runtime_visible_samples() if sample["sample_id"] == sample_id
    )
    return evaluate_detector_runtime_visible_gate_noop(runtime_visible_sample["gate_result"])


def _build_runtime_error_mapping_result(sample_id: str):
    runtime_error_mapping_sample = next(
        sample for sample in _load_runtime_error_mapping_samples() if sample["sample_id"] == sample_id
    )
    visible_gate_result = _build_visible_gate_result(runtime_error_mapping_sample["runtime_visible_sample_id"])
    return evaluate_detector_runtime_error_mapping_noop(visible_gate_result)


def _build_runtime_facing_gate_result(sample_id: str):
    runtime_facing_gate_sample = next(
        sample for sample in _load_runtime_facing_gate_samples() if sample["sample_id"] == sample_id
    )
    runtime_error_mapping_result = _build_runtime_error_mapping_result(
        runtime_facing_gate_sample["runtime_error_mapping_sample_id"]
    )
    return evaluate_detector_runtime_facing_gate_noop(runtime_error_mapping_result)


def _build_runtime_facing_behavior_gate_result(sample_id: str):
    runtime_facing_behavior_gate_sample = next(
        sample for sample in _load_runtime_facing_behavior_gate_samples() if sample["sample_id"] == sample_id
    )
    runtime_facing_gate_result = _build_runtime_facing_gate_result(
        runtime_facing_behavior_gate_sample["runtime_facing_gate_sample_id"]
    )
    return evaluate_detector_runtime_facing_behavior_gate_noop(runtime_facing_gate_result)


def _build_request_profile() -> RequestProfile:
    return RequestProfile.model_validate(
        {
            "method": "GET",
            "url": "https://example.com/search?q=test",
            "response_type": "html",
            "headers": {"User-Agent": "TXT-Reader-Test/1.0"},
            "query": {},
            "body": {},
            "cookies": {},
        }
    )


def test_runtime_facing_behavior_activation_fixture_file_loads_expected_samples():
    samples = _load_samples()

    assert len(samples) >= 4
    sample_ids = {sample["sample_id"] for sample in samples}
    assert "challenge-activation-candidate-carried" in sample_ids
    assert "noop-activation-candidate" in sample_ids


def test_runtime_facing_behavior_activation_input_accepts_behavior_gate_result_and_derived_fields():
    activation_input = prepare_detector_runtime_facing_behavior_activation_input(
        _build_runtime_facing_behavior_gate_result("challenge-behavior-gate-candidate-carried")
    )

    assert activation_input.stage == "search"
    assert activation_input.recommended_error_code == LegadoRuntimeCode.ANTI_BOT_CHALLENGE
    assert (
        activation_input.activation_candidate_kind
        == DetectorRuntimeFacingBehaviorActivationCandidateKind.CHALLENGE_CANDIDATE
    )


def test_runtime_facing_behavior_activation_input_rejects_candidate_kind_mismatch():
    runtime_facing_behavior_gate_result = _build_runtime_facing_behavior_gate_result(
        "challenge-behavior-gate-candidate-carried"
    )

    with pytest.raises(ValidationError):
        DetectorRuntimeFacingBehaviorActivationInput.model_validate(
            {
                "stage": "search",
                "expected_response_type": "html",
                "runtime_facing_behavior_gate_result": runtime_facing_behavior_gate_result,
                "detector_result": runtime_facing_behavior_gate_result.behavior_gate_input.detector_result,
                "recommended_error_code": "LEGADO_ANTI_BOT_CHALLENGE",
                "activation_candidate_kind": "gateway_candidate",
            }
        )


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_evaluate_detector_runtime_facing_behavior_activation_noop_matches_fixture_expectations(sample):
    runtime_facing_behavior_gate_result = _build_runtime_facing_behavior_gate_result(
        sample["runtime_facing_behavior_gate_sample_id"]
    )
    result = evaluate_detector_runtime_facing_behavior_activation_noop(runtime_facing_behavior_gate_result)

    assert result.outcome.value == sample["expected_activation_outcome"]
    assert result.activation_decision == DetectorRuntimeFacingBehaviorActivationDecision.ACTIVATION_DECISION_NOOP
    assert result.activation_input.activation_candidate_kind.value == sample["expected_activation_candidate_kind"]
    if sample["expected_recommended_error_code"] is None:
        assert result.activation_candidate is None
    else:
        assert result.activation_candidate is not None
        assert result.activation_candidate.recommended_error_code is not None
        assert result.activation_candidate.recommended_error_code.value == sample["expected_recommended_error_code"]


def test_build_runtime_facing_behavior_activation_result_requires_candidate_for_candidate_carried():
    activation_input = prepare_detector_runtime_facing_behavior_activation_input(
        _build_runtime_facing_behavior_gate_result("challenge-behavior-gate-candidate-carried")
    )

    with pytest.raises(ValidationError):
        DetectorRuntimeFacingBehaviorActivationResult.model_validate(
            {
                "outcome": DetectorRuntimeFacingBehaviorActivationOutcome.ACTIVATION_CANDIDATE_CARRIED,
                "activation_decision": DetectorRuntimeFacingBehaviorActivationDecision.ACTIVATION_DECISION_NOOP,
                "activation_input": activation_input,
            }
        )


def test_build_runtime_facing_behavior_activation_result_returns_no_candidate_for_no_behavior_gate_candidate():
    activation_input = prepare_detector_runtime_facing_behavior_activation_input(
        _build_runtime_facing_behavior_gate_result("no-behavior-gate-candidate")
    )
    result = build_detector_runtime_facing_behavior_activation_result(activation_input)

    assert result.outcome == DetectorRuntimeFacingBehaviorActivationOutcome.NO_ACTIVATION_CANDIDATE
    assert result.activation_decision == DetectorRuntimeFacingBehaviorActivationDecision.ACTIVATION_DECISION_NOOP
    assert result.activation_candidate is None


def test_execute_stage_success_runs_runtime_facing_behavior_activation_helper_without_changing_response(monkeypatch):
    request_profile = _build_request_profile()
    raw_response = RawFetchResponse(
        requested_url=request_profile.url,
        final_url=request_profile.url,
        status_code=200,
        content_type="text/html; charset=utf-8",
        text="<html><body>ok</body></html>",
        json_data=None,
    )
    observed: dict[str, object] = {}

    monkeypatch.setattr(source_engine, "build_request_profile", lambda **_kwargs: request_profile)
    monkeypatch.setattr(source_engine, "fetch_stage_response", lambda **_kwargs: raw_response)
    monkeypatch.setattr(
        source_engine,
        "observe_live_entry_from_success_response",
        lambda **_kwargs: {"adapter": "ok"},
        raising=False,
    )
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "ok"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: _build_visible_gate_result("challenge-visible-signal-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        lambda *_args, **_kwargs: _build_runtime_error_mapping_result("challenge-mapping-candidate-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_gate_noop",
        lambda *_args, **_kwargs: _build_runtime_facing_gate_result("challenge-gate-candidate-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_gate_noop",
        lambda *_args, **_kwargs: _build_runtime_facing_behavior_gate_result("challenge-behavior-gate-candidate-carried"),
        raising=False,
    )

    def fake_evaluate_activation(runtime_facing_behavior_gate_result):
        observed["runtime_facing_behavior_gate_result"] = runtime_facing_behavior_gate_result
        return {"activation": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_activation_noop",
        fake_evaluate_activation,
        raising=False,
    )

    result = source_engine._execute_stage(
        stage="search",
        stage_request={
            "method": "GET",
            "url": request_profile.url,
            "response_type": request_profile.response_type,
            "headers": {},
            "query": {},
            "body": {},
        },
    )

    assert result is raw_response
    assert observed["runtime_facing_behavior_gate_result"].outcome.value == "behavior_gate_candidate_carried"


def test_execute_stage_error_runs_runtime_facing_behavior_activation_helper_without_changing_error(monkeypatch):
    request_profile = _build_request_profile()
    fetch_error = FetchServiceError(
        "Request timeout while fetching https://example.com/search?q=test",
        code=LegadoRuntimeCode.REQUEST_TIMEOUT,
    )
    observed: dict[str, object] = {}

    monkeypatch.setattr(source_engine, "build_request_profile", lambda **_kwargs: request_profile)

    def fake_fetch_stage_response(**_kwargs):
        raise fetch_error

    monkeypatch.setattr(source_engine, "fetch_stage_response", fake_fetch_stage_response)
    monkeypatch.setattr(
        source_engine,
        "observe_live_entry_from_fetch_error",
        lambda **_kwargs: {"adapter": "error"},
        raising=False,
    )
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "error"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: _build_visible_gate_result("gateway-visible-signal-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        lambda *_args, **_kwargs: _build_runtime_error_mapping_result("gateway-mapping-candidate-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_gate_noop",
        lambda *_args, **_kwargs: _build_runtime_facing_gate_result("gateway-gate-candidate-carried"),
        raising=False,
    )
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_gate_noop",
        lambda *_args, **_kwargs: _build_runtime_facing_behavior_gate_result("gateway-behavior-gate-candidate-carried"),
        raising=False,
    )

    def fake_evaluate_activation(runtime_facing_behavior_gate_result):
        observed["runtime_facing_behavior_gate_result"] = runtime_facing_behavior_gate_result
        return {"activation": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_activation_noop",
        fake_evaluate_activation,
        raising=False,
    )

    with pytest.raises(FetchServiceError, match="Request timeout while fetching"):
        source_engine._execute_stage(
            stage="search",
            stage_request={
                "method": "GET",
                "url": request_profile.url,
                "response_type": request_profile.response_type,
                "headers": {},
                "query": {},
                "body": {},
            },
        )

    assert observed["runtime_facing_behavior_gate_result"].outcome.value == "behavior_gate_candidate_carried"


def test_execute_stage_success_ignores_runtime_facing_behavior_activation_helper_failure(monkeypatch):
    request_profile = _build_request_profile()
    raw_response = RawFetchResponse(
        requested_url=request_profile.url,
        final_url=request_profile.url,
        status_code=200,
        content_type="text/html; charset=utf-8",
        text="<html><body>ok</body></html>",
        json_data=None,
    )

    monkeypatch.setattr(source_engine, "build_request_profile", lambda **_kwargs: request_profile)
    monkeypatch.setattr(source_engine, "fetch_stage_response", lambda **_kwargs: raw_response)
    monkeypatch.setattr(
        source_engine,
        "observe_live_entry_from_success_response",
        lambda **_kwargs: {"adapter": "ok"},
        raising=False,
    )
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_visible_gate_noop", lambda *_args, **_kwargs: {"visible_gate": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_error_mapping_noop", lambda *_args, **_kwargs: {"mapping": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_facing_gate_noop", lambda *_args, **_kwargs: {"gate": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_facing_behavior_gate_noop", lambda *_args, **_kwargs: {"behavior_gate": "ok"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_activation_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal activation failure")),
        raising=False,
    )

    result = source_engine._execute_stage(
        stage="search",
        stage_request={
            "method": "GET",
            "url": request_profile.url,
            "response_type": request_profile.response_type,
            "headers": {},
            "query": {},
            "body": {},
        },
    )

    assert result is raw_response


def test_execute_stage_error_ignores_runtime_facing_behavior_activation_helper_failure(monkeypatch):
    request_profile = _build_request_profile()
    fetch_error = FetchServiceError(
        "Request timeout while fetching https://example.com/search?q=test",
        code=LegadoRuntimeCode.REQUEST_TIMEOUT,
    )

    monkeypatch.setattr(source_engine, "build_request_profile", lambda **_kwargs: request_profile)

    def fake_fetch_stage_response(**_kwargs):
        raise fetch_error

    monkeypatch.setattr(source_engine, "fetch_stage_response", fake_fetch_stage_response)
    monkeypatch.setattr(
        source_engine,
        "observe_live_entry_from_fetch_error",
        lambda **_kwargs: {"adapter": "error"},
        raising=False,
    )
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_visible_gate_noop", lambda *_args, **_kwargs: {"visible_gate": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_error_mapping_noop", lambda *_args, **_kwargs: {"mapping": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_facing_gate_noop", lambda *_args, **_kwargs: {"gate": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_facing_behavior_gate_noop", lambda *_args, **_kwargs: {"behavior_gate": "error"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_facing_behavior_activation_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal activation failure")),
        raising=False,
    )

    with pytest.raises(FetchServiceError, match="Request timeout while fetching"):
        source_engine._execute_stage(
            stage="search",
            stage_request={
                "method": "GET",
                "url": request_profile.url,
                "response_type": request_profile.response_type,
                "headers": {},
                "query": {},
                "body": {},
            },
        )


def test_fetch_service_source_does_not_import_runtime_facing_behavior_activation_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_runtime_facing_behavior_activation_skeleton" not in source


def test_response_guard_source_does_not_import_runtime_facing_behavior_activation_skeleton():
    source = inspect.getsource(response_guard_service)

    assert "detector_runtime_facing_behavior_activation_skeleton" not in source


def test_content_parse_source_does_not_import_runtime_facing_behavior_activation_skeleton():
    source = inspect.getsource(content_parse_service)

    assert "detector_runtime_facing_behavior_activation_skeleton" not in source
