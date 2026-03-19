import inspect
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.schemas.online_detector import (
    DetectorCategory,
    DetectorClassificationResult,
    DetectorDeferredRequirementHint,
    DetectorInput,
    DetectorMatchStatus,
)
from app.schemas.online_runtime import LegadoRuntimeCode
from app.services.online import detector_skeleton, fetch_service
from app.services.online.fetch_service import fetch_stage_response


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "online_detector_samples.json"


def _load_samples():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_detector_input(**overrides):
    payload = {
        "stage": "search",
        "expected_response_type": "html",
        "requested_url": "https://example.com/search?q=test",
        "final_url": "https://example.com/search?q=test",
        "status_code": 200,
        "content_type": "text/html; charset=utf-8",
        "redirected": False,
        "body_text_preview": "<html><body>ok</body></html>",
        "body_text_length": 28,
    }
    payload.update(overrides)
    return payload


def _build_response(*, status_code: int = 200, content_type: str = "text/html; charset=utf-8", content: str = "<html><body>ok</body></html>") -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/search")
    return httpx.Response(
        status_code=status_code,
        headers={"content-type": content_type},
        content=content.encode("utf-8"),
        request=request,
    )


def test_detector_input_accepts_valid_payload():
    detector_input = DetectorInput.model_validate(_build_detector_input())

    assert detector_input.stage == "search"
    assert detector_input.redirected is False


def test_detector_input_rejects_overlong_body_text_preview():
    with pytest.raises(ValidationError):
        DetectorInput.model_validate(
            _build_detector_input(body_text_preview="x" * 4097, body_text_length=4097)
        )


def test_detector_input_rejects_missing_required_field():
    payload = _build_detector_input()
    payload.pop("stage")

    with pytest.raises(ValidationError):
        DetectorInput.model_validate(payload)


@pytest.mark.parametrize(
    ("status", "category", "error_code"),
    [
        (DetectorMatchStatus.NO_MATCH, DetectorCategory.NO_MATCH, None),
        (
            DetectorMatchStatus.CANDIDATE_MATCH,
            DetectorCategory.CHALLENGE_CANDIDATE,
            LegadoRuntimeCode.ANTI_BOT_CHALLENGE,
        ),
        (
            DetectorMatchStatus.DEFERRED,
            DetectorCategory.NO_MATCH,
            LegadoRuntimeCode.JS_EXECUTION_REQUIRED,
        ),
    ],
)
def test_detector_classification_result_accepts_expected_statuses(status, category, error_code):
    result = DetectorClassificationResult.model_validate(
        {
            "category": category,
            "status": status,
            "matched_signals": [],
            "evidence_snippets": [],
            "recommended_error_code": error_code,
            "deferred_requirement_hint": DetectorDeferredRequirementHint.NONE,
        }
    )

    assert result.status == status


def test_detector_sample_fixtures_load_and_cover_positive_and_negative_cases():
    samples = _load_samples()

    assert len(samples) >= 6
    categories = {sample["expected_category"] for sample in samples}
    assert "challenge_candidate" in categories
    assert "gateway_candidate" in categories
    assert "no_match" in categories


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda sample: sample["sample_id"])
def test_detector_skeleton_classifies_fixture_samples(sample):
    detector_input = DetectorInput.model_validate(
        {
            "stage": sample["stage"],
            "expected_response_type": "html",
            "requested_url": sample["requested_url"],
            "final_url": sample["final_url"],
            "status_code": sample["status_code"],
            "content_type": sample["content_type"],
            "redirected": sample["redirected"],
            "body_text_preview": sample["body_text_preview"],
            "body_text_length": len(sample["body_text_preview"]),
        }
    )

    result = detector_skeleton.classify_detector_input(detector_input)

    assert result.category.value == sample["expected_category"]
    assert result.status.value == sample["expected_status"]
    assert (
        result.recommended_error_code.value if result.recommended_error_code is not None else None
    ) == sample["expected_recommended_error_code"]
    assert result.matched_signals == sample["expected_matched_signals"]


def test_detector_skeleton_does_not_implement_suspicious_html_or_browser_js_categories():
    detector_input = DetectorInput.model_validate(
        _build_detector_input(
            status_code=200,
            body_text_preview="<html><body>unexpected html body</body></html>",
            body_text_length=46,
        )
    )

    result = detector_skeleton.classify_detector_input(detector_input)

    assert result.category == DetectorCategory.NO_MATCH
    assert result.status == DetectorMatchStatus.NO_MATCH
    assert result.recommended_error_code is None


def test_detector_skeleton_is_not_referenced_by_fetch_service_live_path(monkeypatch):
    monkeypatch.setattr(
        detector_skeleton,
        "classify_detector_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("detector skeleton must remain offline")),
    )

    def fake_request(**_kwargs):
        return _build_response()

    monkeypatch.setattr(httpx, "request", fake_request)

    response = fetch_stage_response(
        method="GET",
        url="https://example.com/search",
        response_type="html",
    )

    assert response.status_code == 200


def test_fetch_service_source_does_not_import_detector_skeleton():
    source = inspect.getsource(fetch_service)

    assert "detector_skeleton" not in source
