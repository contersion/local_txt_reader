import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.online_runtime import LegadoRuntimeCode, RequestProfile
from app.services.online import content_parse_service, fetch_service, response_guard_service, source_engine
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse
from app.services.online.detector_runtime_visible_gating_skeleton import evaluate_detector_runtime_visible_gate_noop
from app.services.online.detector_runtime_error_mapping_skeleton import (
    build_detector_runtime_error_mapping_result,
    evaluate_detector_runtime_error_mapping_noop,
    prepare_detector_runtime_error_mapping_input,
)
from app.schemas.online_detector_runtime_error_mapping import (
    DetectorRuntimeErrorMappingCandidateKind,
    DetectorRuntimeErrorMappingDecision,
    DetectorRuntimeErrorMappingInput,
    DetectorRuntimeErrorMappingOutcome,
    DetectorRuntimeErrorMappingResult,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_error_mapping_samples.json"
RUNTIME_VISIBLE_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_visible_gating_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_runtime_visible_samples():
    return json.loads(RUNTIME_VISIBLE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_visible_gate_result(sample_id: str):
    runtime_visible_sample = next(
        sample for sample in _load_runtime_visible_samples() if sample["sample_id"] == sample_id
    )
    return evaluate_detector_runtime_visible_gate_noop(runtime_visible_sample["gate_result"])


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


def test_runtime_error_mapping_fixture_file_loads_expected_samples():
    samples = _load_samples()

    assert len(samples) >= 4
    sample_ids = {sample["sample_id"] for sample in samples}
    assert "challenge-mapping-candidate-carried" in sample_ids
    assert "noop-visible-no-mapping-candidate" in sample_ids


def test_runtime_error_mapping_input_accepts_visible_gate_result_and_derived_fields():
    mapping_input = prepare_detector_runtime_error_mapping_input(
        _build_visible_gate_result("challenge-visible-signal-carried")
    )

    assert mapping_input.stage == "search"
    assert mapping_input.recommended_error_code == LegadoRuntimeCode.ANTI_BOT_CHALLENGE
    assert mapping_input.mapping_candidate_kind == DetectorRuntimeErrorMappingCandidateKind.CHALLENGE_CANDIDATE


def test_runtime_error_mapping_input_rejects_mapping_candidate_kind_mismatch():
    visible_gate_result = _build_visible_gate_result("challenge-visible-signal-carried")

    with pytest.raises(ValidationError):
        DetectorRuntimeErrorMappingInput.model_validate(
            {
                "stage": "search",
                "expected_response_type": "html",
                "visible_gate_result": visible_gate_result,
                "detector_result": visible_gate_result.visible_gate_input.detector_result,
                "recommended_error_code": "LEGADO_ANTI_BOT_CHALLENGE",
                "mapping_candidate_kind": "gateway_candidate",
            }
        )


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_evaluate_detector_runtime_error_mapping_noop_matches_fixture_expectations(sample):
    visible_gate_result = _build_visible_gate_result(sample["runtime_visible_sample_id"])
    result = evaluate_detector_runtime_error_mapping_noop(visible_gate_result)

    assert result.outcome.value == sample["expected_mapping_outcome"]
    assert result.mapping_decision == DetectorRuntimeErrorMappingDecision.MAPPING_DECISION_NOOP
    assert result.mapping_input.mapping_candidate_kind.value == sample["expected_mapping_candidate_kind"]
    if sample["expected_recommended_error_code"] is None:
        assert result.mapping_candidate is None
    else:
        assert result.mapping_candidate is not None
        assert result.mapping_candidate.recommended_error_code is not None
        assert result.mapping_candidate.recommended_error_code.value == sample["expected_recommended_error_code"]


def test_build_runtime_error_mapping_result_requires_candidate_for_mapping_candidate_carried():
    mapping_input = prepare_detector_runtime_error_mapping_input(
        _build_visible_gate_result("challenge-visible-signal-carried")
    )

    with pytest.raises(ValidationError):
        DetectorRuntimeErrorMappingResult.model_validate(
            {
                "outcome": DetectorRuntimeErrorMappingOutcome.MAPPING_CANDIDATE_CARRIED,
                "mapping_decision": DetectorRuntimeErrorMappingDecision.MAPPING_DECISION_NOOP,
                "mapping_input": mapping_input,
            }
        )


def test_build_runtime_error_mapping_result_returns_no_candidate_for_no_visible_signal():
    mapping_input = prepare_detector_runtime_error_mapping_input(
        _build_visible_gate_result("no-visible-signal")
    )
    result = build_detector_runtime_error_mapping_result(mapping_input)

    assert result.outcome == DetectorRuntimeErrorMappingOutcome.NO_MAPPING_CANDIDATE
    assert result.mapping_decision == DetectorRuntimeErrorMappingDecision.MAPPING_DECISION_NOOP
    assert result.mapping_candidate is None


def test_execute_stage_success_runs_runtime_error_mapping_helper_without_changing_response(monkeypatch):
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
    monkeypatch.setattr(source_engine, "observe_live_entry_from_success_response", lambda **_kwargs: {"adapter": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "ok"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: _build_visible_gate_result("challenge-visible-signal-carried"),
        raising=False,
    )

    def fake_evaluate_mapping(visible_gate_result):
        observed["visible_gate_result"] = visible_gate_result
        return {"mapping": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        fake_evaluate_mapping,
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
    assert observed["visible_gate_result"].outcome.value == "visible_signal_carried"


def test_execute_stage_error_runs_runtime_error_mapping_helper_without_changing_error(monkeypatch):
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
    monkeypatch.setattr(source_engine, "observe_live_entry_from_fetch_error", lambda **_kwargs: {"adapter": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "error"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: _build_visible_gate_result("gateway-visible-signal-carried"),
        raising=False,
    )

    def fake_evaluate_mapping(visible_gate_result):
        observed["visible_gate_result"] = visible_gate_result
        return {"mapping": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        fake_evaluate_mapping,
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

    assert observed["visible_gate_result"].outcome.value == "visible_signal_carried"


def test_execute_stage_success_ignores_runtime_error_mapping_helper_failure(monkeypatch):
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
    monkeypatch.setattr(source_engine, "observe_live_entry_from_success_response", lambda **_kwargs: {"adapter": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "ok"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_visible_gate_noop", lambda *_args, **_kwargs: {"visible_gate": "ok"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal mapping failure")),
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


def test_execute_stage_error_ignores_runtime_error_mapping_helper_failure(monkeypatch):
    request_profile = _build_request_profile()
    fetch_error = FetchServiceError(
        "Request timeout while fetching https://example.com/search?q=test",
        code=LegadoRuntimeCode.REQUEST_TIMEOUT,
    )

    monkeypatch.setattr(source_engine, "build_request_profile", lambda **_kwargs: request_profile)

    def fake_fetch_stage_response(**_kwargs):
        raise fetch_error

    monkeypatch.setattr(source_engine, "fetch_stage_response", fake_fetch_stage_response)
    monkeypatch.setattr(source_engine, "observe_live_entry_from_fetch_error", lambda **_kwargs: {"adapter": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_behavior_gate_noop", lambda *_args, **_kwargs: {"gate": "error"}, raising=False)
    monkeypatch.setattr(source_engine, "evaluate_detector_runtime_visible_gate_noop", lambda *_args, **_kwargs: {"visible_gate": "error"}, raising=False)
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_error_mapping_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal mapping failure")),
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


def test_fetch_service_source_does_not_import_runtime_error_mapping_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_runtime_error_mapping_skeleton" not in source


def test_response_guard_source_does_not_import_runtime_error_mapping_skeleton():
    source = inspect.getsource(response_guard_service)

    assert "detector_runtime_error_mapping_skeleton" not in source


def test_content_parse_source_does_not_import_runtime_error_mapping_skeleton():
    source = inspect.getsource(content_parse_service)

    assert "detector_runtime_error_mapping_skeleton" not in source
