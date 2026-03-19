import inspect
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.schemas.online_detector import DetectorCategory, DetectorClassificationResult, DetectorMatchStatus
from app.schemas.online_detector_adapter import (
    DetectorAdapterInput,
    DetectorAdapterOutcome,
    DetectorAdapterOutput,
)
from app.services.online import detector_skeleton, fetch_service, response_guard_service, source_engine
from app.services.online.detector_adapter_skeleton import (
    coerce_detector_adapter_output_contract,
    prepare_detector_adapter_input,
    prepare_detector_adapter_output_noop,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_adapter_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_adapter_fixture_file_loads_input_and_output_samples():
    samples = _load_samples()

    assert len(samples) >= 5
    kinds = {sample["sample_kind"] for sample in samples}
    assert "adapter_input" in kinds
    assert "adapter_output" in kinds


def test_detector_adapter_input_accepts_success_summary_payload():
    adapter_input = DetectorAdapterInput.model_validate(
        {
            "stage": "search",
            "expected_response_type": "html",
            "fetch_outcome_summary": {
                "stage": "search",
                "expected_response_type": "html",
                "requested_url": "https://example.com/search?q=test",
                "fetch_outcome_kind": "success",
            },
        }
    )

    assert adapter_input.stage == "search"
    assert adapter_input.fetch_outcome_summary.fetch_outcome_kind.value == "success"


def test_detector_adapter_input_accepts_error_summary_payload():
    adapter_input = DetectorAdapterInput.model_validate(
        {
            "stage": "content",
            "expected_response_type": "html",
            "fetch_outcome_summary": {
                "stage": "content",
                "expected_response_type": "html",
                "requested_url": "https://example.com/content/1",
                "fetch_outcome_kind": "transport_error",
                "exception_kind": "timeout",
            },
        }
    )

    assert adapter_input.stage == "content"
    assert adapter_input.fetch_outcome_summary.fetch_outcome_kind.value == "transport_error"


def test_detector_adapter_input_rejects_stage_mismatch():
    with pytest.raises(ValidationError):
        DetectorAdapterInput.model_validate(
            {
                "stage": "search",
                "expected_response_type": "html",
                "fetch_outcome_summary": {
                    "stage": "detail",
                    "expected_response_type": "html",
                    "requested_url": "https://example.com/detail/1",
                    "fetch_outcome_kind": "success",
                },
            }
        )


def test_detector_adapter_output_accepts_noop_shape():
    output = DetectorAdapterOutput.model_validate(
        {
            "outcome": DetectorAdapterOutcome.NOOP,
            "adapter_input": {
                "stage": "search",
                "expected_response_type": "html",
                "fetch_outcome_summary": {
                    "stage": "search",
                    "expected_response_type": "html",
                    "requested_url": "https://example.com/search?q=test",
                    "fetch_outcome_kind": "success",
                },
            },
        }
    )

    assert output.outcome == DetectorAdapterOutcome.NOOP
    assert output.detector_input is None
    assert output.detector_result is None


def test_detector_adapter_output_requires_detector_input_for_prepared_outcome():
    with pytest.raises(ValidationError):
        DetectorAdapterOutput.model_validate(
            {
                "outcome": DetectorAdapterOutcome.DETECTOR_INPUT_PREPARED,
                "adapter_input": {
                    "stage": "search",
                    "expected_response_type": "html",
                    "fetch_outcome_summary": {
                        "stage": "search",
                        "expected_response_type": "html",
                        "requested_url": "https://example.com/search?q=test",
                        "fetch_outcome_kind": "success",
                    },
                },
            }
        )


def test_detector_adapter_output_requires_detector_result_for_result_attached_outcome():
    with pytest.raises(ValidationError):
        DetectorAdapterOutput.model_validate(
            {
                "outcome": DetectorAdapterOutcome.DETECTOR_RESULT_ATTACHED,
                "adapter_input": {
                    "stage": "search",
                    "expected_response_type": "html",
                    "fetch_outcome_summary": {
                        "stage": "search",
                        "expected_response_type": "html",
                        "requested_url": "https://example.com/search?q=test",
                        "fetch_outcome_kind": "success",
                    },
                },
                "detector_input": {
                    "stage": "search",
                    "expected_response_type": "html",
                    "requested_url": "https://example.com/search?q=test",
                    "final_url": "https://example.com/search?q=test",
                    "status_code": 200,
                    "content_type": "text/html; charset=utf-8",
                    "redirected": False,
                    "body_text_preview": "<html><body>ok</body></html>",
                    "body_text_length": 28,
                },
            }
        )


def test_prepare_detector_adapter_input_accepts_success_summary_stub():
    adapter_input = prepare_detector_adapter_input(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
        }
    )

    assert isinstance(adapter_input, DetectorAdapterInput)
    assert adapter_input.fetch_outcome_summary.fetch_outcome_kind.value == "success"


def test_prepare_detector_adapter_input_accepts_error_summary_stub():
    adapter_input = prepare_detector_adapter_input(
        {
            "stage": "catalog",
            "expected_response_type": "html",
            "requested_url": "https://example.com/catalog/1",
            "fetch_outcome_kind": "http_error",
            "status_code": 403,
        }
    )

    assert isinstance(adapter_input, DetectorAdapterInput)
    assert adapter_input.fetch_outcome_summary.fetch_outcome_kind.value == "http_error"


def test_prepare_detector_adapter_output_noop_returns_noop_output():
    adapter_input = prepare_detector_adapter_input(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
        }
    )

    output = prepare_detector_adapter_output_noop(adapter_input)

    assert output.outcome == DetectorAdapterOutcome.NOOP
    assert output.detector_input is None
    assert output.detector_result is None


def test_coerce_detector_adapter_output_contract_supports_result_attached_shape():
    output = coerce_detector_adapter_output_contract(
        {
            "outcome": "detector_result_attached",
            "adapter_input": {
                "stage": "detail",
                "expected_response_type": "html",
                "fetch_outcome_summary": {
                    "stage": "detail",
                    "expected_response_type": "html",
                    "requested_url": "https://example.com/detail/1",
                    "fetch_outcome_kind": "http_error",
                    "status_code": 403,
                },
            },
            "detector_input": {
                "stage": "detail",
                "expected_response_type": "html",
                "requested_url": "https://example.com/detail/1",
                "final_url": "https://example.com/challenge",
                "status_code": 403,
                "content_type": "text/html; charset=utf-8",
                "redirected": True,
                "body_text_preview": "<html><title>Checking your browser</title></html>",
                "body_text_length": 50,
            },
            "detector_result": {
                "category": DetectorCategory.CHALLENGE_CANDIDATE,
                "status": DetectorMatchStatus.CANDIDATE_MATCH,
                "matched_signals": ["challenge_browser_check"],
                "evidence_snippets": ["challenge_browser_check :: checking your browser"],
                "recommended_error_code": "LEGADO_ANTI_BOT_CHALLENGE",
                "deferred_requirement_hint": "none",
            },
        }
    )

    assert output.outcome == DetectorAdapterOutcome.DETECTOR_RESULT_ATTACHED
    assert isinstance(output.detector_result, DetectorClassificationResult)


def test_adapter_helper_rejects_live_httpx_response_and_exception_objects():
    request = httpx.Request("GET", "https://example.com/search")
    response = httpx.Response(200, request=request)

    with pytest.raises(TypeError):
        prepare_detector_adapter_input(response)

    with pytest.raises(TypeError):
        coerce_detector_adapter_output_contract(httpx.TimeoutException("timeout"))


def test_adapter_helper_does_not_call_detector_classifier(monkeypatch):
    monkeypatch.setattr(
        detector_skeleton,
        "classify_detector_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("adapter skeleton must not invoke detector classifier")
        ),
    )

    adapter_input = prepare_detector_adapter_input(
        {
            "stage": "search",
            "expected_response_type": "html",
            "requested_url": "https://example.com/search?q=test",
            "fetch_outcome_kind": "success",
        }
    )
    output = prepare_detector_adapter_output_noop(adapter_input)

    assert output.outcome == DetectorAdapterOutcome.NOOP


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_adapter_fixtures_coerce_to_expected_contract(sample):
    if sample["sample_kind"] == "adapter_input":
        result = DetectorAdapterInput.model_validate(sample["payload"])
    else:
        result = coerce_detector_adapter_output_contract(sample["payload"])

    assert result.__class__.__name__ == sample["expected_model"]


def test_fetch_service_source_does_not_import_detector_adapter_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_adapter_skeleton" not in source


def test_source_engine_source_does_not_import_detector_adapter_skeleton():
    source = inspect.getsource(source_engine)

    assert "detector_adapter_skeleton" not in source


def test_response_guard_source_does_not_import_detector_adapter_skeleton():
    source = inspect.getsource(response_guard_service)

    assert "detector_adapter_skeleton" not in source
