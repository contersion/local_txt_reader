import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.online_detector_runtime_visible_gate import (
    DetectorRuntimeVisibleGateDecision,
    DetectorRuntimeVisibleGateInput,
    DetectorRuntimeVisibleGateOutcome,
    DetectorRuntimeVisibleGateResult,
)
from app.schemas.online_runtime import LegadoRuntimeCode, RequestProfile
from app.services.online import content_parse_service, fetch_service, response_guard_service, source_engine
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse
from app.services.online.detector_runtime_visible_gating_skeleton import (
    build_detector_runtime_visible_gate_result,
    evaluate_detector_runtime_visible_gate_noop,
    prepare_detector_runtime_visible_gate_input,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_runtime_visible_gating_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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


def test_runtime_visible_fixture_file_loads_expected_samples():
    samples = _load_samples()

    assert len(samples) >= 4
    sample_ids = {sample["sample_id"] for sample in samples}
    assert "challenge-visible-signal-carried" in sample_ids
    assert "noop-visible-signal" in sample_ids


def test_runtime_visible_gate_input_accepts_gate_result_and_derived_fields():
    visible_input = DetectorRuntimeVisibleGateInput.model_validate(
        {
            "stage": "search",
            "expected_response_type": "html",
            "gate_result": _load_samples()[0]["gate_result"],
            "adapter_output": _load_samples()[0]["gate_result"]["gate_input"]["adapter_output"],
            "detector_result": _load_samples()[0]["gate_result"]["gate_input"]["detector_result"],
            "recommended_error_code": "LEGADO_ANTI_BOT_CHALLENGE",
        }
    )

    assert visible_input.stage == "search"
    assert visible_input.recommended_error_code == LegadoRuntimeCode.ANTI_BOT_CHALLENGE


def test_runtime_visible_gate_input_rejects_recommended_error_code_mismatch():
    with pytest.raises(ValidationError):
        DetectorRuntimeVisibleGateInput.model_validate(
            {
                "stage": "search",
                "expected_response_type": "html",
                "gate_result": _load_samples()[0]["gate_result"],
                "adapter_output": _load_samples()[0]["gate_result"]["gate_input"]["adapter_output"],
                "detector_result": _load_samples()[0]["gate_result"]["gate_input"]["detector_result"],
                "recommended_error_code": "LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY",
            }
        )


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_evaluate_detector_runtime_visible_gate_noop_matches_fixture_expectations(sample):
    result = evaluate_detector_runtime_visible_gate_noop(sample["gate_result"])

    assert result.outcome.value == sample["expected_visible_outcome"]
    assert result.visible_gate_decision == DetectorRuntimeVisibleGateDecision.VISIBLE_GATE_DECISION_NOOP
    if sample["expected_recommended_error_code"] is None:
        assert result.runtime_visible_signal is None
    else:
        assert result.runtime_visible_signal is not None
        assert (
            result.runtime_visible_signal.recommended_error_code.value
            if result.runtime_visible_signal.recommended_error_code is not None
            else None
        ) == sample["expected_recommended_error_code"]


def test_build_runtime_visible_gate_result_requires_signal_for_visible_signal_carried():
    visible_input = prepare_detector_runtime_visible_gate_input(_load_samples()[0]["gate_result"])

    with pytest.raises(ValidationError):
        DetectorRuntimeVisibleGateResult.model_validate(
            {
                "outcome": DetectorRuntimeVisibleGateOutcome.VISIBLE_SIGNAL_CARRIED,
                "visible_gate_decision": DetectorRuntimeVisibleGateDecision.VISIBLE_GATE_DECISION_NOOP,
                "visible_gate_input": visible_input,
            }
        )


def test_prepare_runtime_visible_gate_input_reads_gate_result_and_error_code():
    visible_input = prepare_detector_runtime_visible_gate_input(_load_samples()[1]["gate_result"])

    assert visible_input.detector_result is not None
    assert visible_input.recommended_error_code == LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY


def test_build_runtime_visible_gate_result_returns_no_signal_for_no_signal():
    visible_input = prepare_detector_runtime_visible_gate_input(_load_samples()[2]["gate_result"])
    result = build_detector_runtime_visible_gate_result(visible_input)

    assert result.outcome == DetectorRuntimeVisibleGateOutcome.NO_VISIBLE_SIGNAL
    assert result.visible_gate_decision == DetectorRuntimeVisibleGateDecision.VISIBLE_GATE_DECISION_NOOP
    assert result.runtime_visible_signal is None


def test_execute_stage_success_runs_runtime_visible_helper_without_changing_response(monkeypatch):
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

    def fake_evaluate_runtime_visible(gate_result):
        observed["gate_result"] = gate_result
        return {"visible_gate": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        fake_evaluate_runtime_visible,
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
    assert observed["gate_result"] == {"gate": "ok"}


def test_execute_stage_error_runs_runtime_visible_helper_without_changing_error(monkeypatch):
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

    def fake_evaluate_runtime_visible(gate_result):
        observed["gate_result"] = gate_result
        return {"visible_gate": "noop"}

    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        fake_evaluate_runtime_visible,
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

    assert observed["gate_result"] == {"gate": "error"}


def test_execute_stage_success_ignores_runtime_visible_helper_failure(monkeypatch):
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
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal visible gate failure")),
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


def test_execute_stage_error_ignores_runtime_visible_helper_failure(monkeypatch):
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
    monkeypatch.setattr(
        source_engine,
        "evaluate_detector_runtime_visible_gate_noop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("internal visible gate failure")),
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


def test_fetch_service_source_does_not_import_runtime_visible_gating_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_runtime_visible_gating_skeleton" not in source


def test_response_guard_source_does_not_import_runtime_visible_gating_skeleton():
    source = inspect.getsource(response_guard_service)

    assert "detector_runtime_visible_gating_skeleton" not in source


def test_content_parse_source_does_not_import_runtime_visible_gating_skeleton():
    source = inspect.getsource(content_parse_service)

    assert "detector_runtime_visible_gating_skeleton" not in source
