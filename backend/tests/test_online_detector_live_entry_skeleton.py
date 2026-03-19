import inspect
import json
from pathlib import Path

import pytest

from app.schemas.online_detector_adapter import DetectorAdapterOutcome
from app.schemas.online_runtime import LegadoRuntimeCode, RequestProfile
from app.services.online import content_parse_service, fetch_service, response_guard_service, source_engine
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse
from app.services.online.detector_live_entry_skeleton import (
    observe_live_entry_from_fetch_error,
    observe_live_entry_from_success_response,
    observe_live_entry_from_summary,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_live_entry_samples.json"


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


def test_live_entry_fixture_file_loads_expected_samples():
    samples = _load_samples()

    assert len(samples) >= 4
    sample_ids = {sample["sample_id"] for sample in samples}
    assert "success-challenge-candidate" in sample_ids
    assert "error-gateway-candidate" in sample_ids


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_live_entry_from_summary_matches_fixture_expectations(sample):
    output = observe_live_entry_from_summary(sample["payload"])

    assert output.outcome.value == sample["expected_adapter_outcome"]
    if sample["expected_detector_category"] is None:
        assert output.detector_result is None
        return

    assert output.detector_result is not None
    assert output.detector_result.category.value == sample["expected_detector_category"]
    assert output.detector_result.status.value == sample["expected_detector_status"]
    assert (
        output.detector_result.recommended_error_code.value
        if output.detector_result.recommended_error_code is not None
        else None
    ) == sample["expected_recommended_error_code"]


def test_observe_live_entry_from_success_response_attaches_detector_result():
    raw_response = RawFetchResponse(
        requested_url="https://example.com/search?q=test",
        final_url="https://example.com/search?q=test",
        status_code=200,
        content_type="text/html; charset=utf-8",
        text="Checking your browser. Enable JavaScript and cookies to continue.",
        json_data=None,
    )

    output = observe_live_entry_from_success_response(
        stage="search",
        expected_response_type="html",
        raw_response=raw_response,
    )

    assert output.outcome == DetectorAdapterOutcome.DETECTOR_RESULT_ATTACHED
    assert output.detector_result is not None
    assert output.detector_result.recommended_error_code == LegadoRuntimeCode.ANTI_BOT_CHALLENGE


def test_observe_live_entry_from_fetch_error_returns_noop_for_timeout():
    error = FetchServiceError(
        "Request timeout while fetching https://example.com/search?q=test",
        code=LegadoRuntimeCode.REQUEST_TIMEOUT,
    )

    output = observe_live_entry_from_fetch_error(
        stage="search",
        expected_response_type="html",
        requested_url="https://example.com/search?q=test",
        error=error,
    )

    assert output.outcome == DetectorAdapterOutcome.NOOP
    assert output.detector_result is None


def test_execute_stage_success_runs_live_entry_helper_without_changing_response(monkeypatch):
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

    def fake_observe_success(*, stage, expected_response_type, raw_response):
        observed["stage"] = stage
        observed["expected_response_type"] = expected_response_type
        observed["raw_response"] = raw_response
        return object()

    monkeypatch.setattr(source_engine, "observe_live_entry_from_success_response", fake_observe_success, raising=False)

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
    assert observed["stage"] == "search"
    assert observed["expected_response_type"] == "html"
    assert observed["raw_response"] is raw_response


def test_execute_stage_error_runs_live_entry_helper_without_changing_error(monkeypatch):
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

    def fake_observe_error(*, stage, expected_response_type, requested_url, error):
        observed["stage"] = stage
        observed["expected_response_type"] = expected_response_type
        observed["requested_url"] = requested_url
        observed["error"] = error
        return object()

    monkeypatch.setattr(source_engine, "observe_live_entry_from_fetch_error", fake_observe_error, raising=False)

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

    assert observed["stage"] == "search"
    assert observed["expected_response_type"] == "html"
    assert observed["requested_url"] == request_profile.url
    assert observed["error"] is fetch_error


def test_execute_stage_success_ignores_live_entry_helper_failure(monkeypatch):
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
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("internal live-entry failure")),
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


def test_execute_stage_error_ignores_live_entry_helper_failure(monkeypatch):
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
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("internal live-entry failure")),
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


def test_fetch_service_source_does_not_import_live_entry_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_live_entry_skeleton" not in source


def test_response_guard_source_does_not_import_live_entry_skeleton():
    source = inspect.getsource(response_guard_service)

    assert "detector_live_entry_skeleton" not in source


def test_content_parse_source_does_not_import_live_entry_skeleton():
    source = inspect.getsource(content_parse_service)

    assert "detector_live_entry_skeleton" not in source
