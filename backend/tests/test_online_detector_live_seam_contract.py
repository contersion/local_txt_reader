import inspect
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.schemas.online_live_seam import (
    FetchErrorSummary,
    FetchExceptionKind,
    FetchOutcomeKind,
    FetchSuccessSummary,
)
from app.services.online import detector_skeleton, fetch_service, source_engine
from app.services.online.live_seam_skeleton import (
    build_error_summary_from_stub,
    build_success_summary_from_stub,
    coerce_fetch_outcome_summary,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_live_seam_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_live_seam_fixture_file_loads_success_and_error_samples():
    samples = _load_samples()

    assert len(samples) >= 6
    kinds = {sample["payload"]["fetch_outcome_kind"] for sample in samples}
    assert "success" in kinds
    assert "http_error" in kinds
    assert "transport_error" in kinds


def test_fetch_success_summary_accepts_minimal_success_payload():
    summary = FetchSuccessSummary.model_validate(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": FetchOutcomeKind.SUCCESS,
        }
    )

    assert summary.fetch_outcome_kind == FetchOutcomeKind.SUCCESS
    assert summary.final_url is None
    assert summary.exception_kind is None


def test_fetch_error_summary_accepts_http_error_payload():
    summary = FetchErrorSummary.model_validate(
        {
            "stage": "detail",
            "expected_response_type": "html",
            "requested_url": "https://example.com/detail/1",
            "fetch_outcome_kind": FetchOutcomeKind.HTTP_ERROR,
            "status_code": 403,
            "content_type": "text/html; charset=utf-8",
            "body_text_preview": "<html><title>Access denied</title></html>",
            "body_text_length": 40,
        }
    )

    assert summary.fetch_outcome_kind == FetchOutcomeKind.HTTP_ERROR
    assert summary.status_code == 403
    assert summary.exception_kind is None


def test_fetch_error_summary_accepts_transport_error_payload():
    summary = FetchErrorSummary.model_validate(
        {
            "stage": "catalog",
            "expected_response_type": "html",
            "requested_url": "https://example.com/catalog/1",
            "fetch_outcome_kind": FetchOutcomeKind.TRANSPORT_ERROR,
            "exception_kind": FetchExceptionKind.TIMEOUT,
        }
    )

    assert summary.fetch_outcome_kind == FetchOutcomeKind.TRANSPORT_ERROR
    assert summary.exception_kind == FetchExceptionKind.TIMEOUT
    assert summary.status_code is None


def test_fetch_success_summary_rejects_missing_required_field():
    with pytest.raises(ValidationError):
        FetchSuccessSummary.model_validate(
            {
                "expected_response_type": "html",
                "requested_url": "https://example.com/search",
                "fetch_outcome_kind": FetchOutcomeKind.SUCCESS,
            }
        )


def test_fetch_error_summary_rejects_transport_error_without_exception_kind():
    with pytest.raises(ValidationError):
        FetchErrorSummary.model_validate(
            {
                "stage": "content",
                "expected_response_type": "html",
                "requested_url": "https://example.com/content/1",
                "fetch_outcome_kind": FetchOutcomeKind.TRANSPORT_ERROR,
            }
        )


def test_fetch_error_summary_rejects_http_error_without_status_code():
    with pytest.raises(ValidationError):
        FetchErrorSummary.model_validate(
            {
                "stage": "content",
                "expected_response_type": "html",
                "requested_url": "https://example.com/content/1",
                "fetch_outcome_kind": FetchOutcomeKind.HTTP_ERROR,
            }
        )


def test_build_success_summary_from_stub_returns_success_summary():
    summary = build_success_summary_from_stub(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
            "final_url": "https://example.com/search?q=test",
            "status_code": 200,
        }
    )

    assert isinstance(summary, FetchSuccessSummary)
    assert summary.status_code == 200


def test_build_error_summary_from_stub_returns_error_summary():
    summary = build_error_summary_from_stub(
        {
            "stage": "detail",
            "expected_response_type": "html",
            "requested_url": "https://example.com/detail/1",
            "fetch_outcome_kind": "http_error",
            "status_code": 503,
            "content_type": "text/html",
        }
    )

    assert isinstance(summary, FetchErrorSummary)
    assert summary.status_code == 503


def test_coerce_fetch_outcome_summary_uses_fetch_outcome_kind():
    success_summary = coerce_fetch_outcome_summary(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
        }
    )
    error_summary = coerce_fetch_outcome_summary(
        {
            "stage": "content",
            "expected_response_type": "html",
            "requested_url": "https://example.com/content/1",
            "fetch_outcome_kind": "transport_error",
            "exception_kind": "timeout",
        }
    )

    assert isinstance(success_summary, FetchSuccessSummary)
    assert isinstance(error_summary, FetchErrorSummary)


def test_live_seam_helpers_reject_httpx_response_and_exception_objects():
    request = httpx.Request("GET", "https://example.com/search")
    response = httpx.Response(200, request=request)

    with pytest.raises(TypeError):
        build_success_summary_from_stub(response)

    with pytest.raises(TypeError):
        build_error_summary_from_stub(httpx.TimeoutException("timeout"))


def test_live_seam_helpers_do_not_call_detector_classifier(monkeypatch):
    monkeypatch.setattr(
        detector_skeleton,
        "classify_detector_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("live seam contract helpers must not run detector classification")
        ),
    )

    summary = build_success_summary_from_stub(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
        }
    )

    assert isinstance(summary, FetchSuccessSummary)


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_live_seam_fixtures_coerce_to_expected_summary_type(sample):
    summary = coerce_fetch_outcome_summary(sample["payload"])

    assert summary.fetch_outcome_kind.value == sample["payload"]["fetch_outcome_kind"]
    assert summary.__class__.__name__ == sample["expected_summary_model"]


def test_fetch_service_source_does_not_import_live_seam_skeleton():
    source = inspect.getsource(fetch_service)

    assert "live_seam_skeleton" not in source


def test_source_engine_source_does_not_import_live_seam_skeleton():
    source = inspect.getsource(source_engine)

    assert "live_seam_skeleton" not in source
