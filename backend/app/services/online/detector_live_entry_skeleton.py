import re
from collections.abc import Mapping
from typing import Any

from app.schemas.online_detector import DetectorInput
from app.schemas.online_detector_adapter import DetectorAdapterOutput, DetectorAdapterOutcome
from app.schemas.online_live_seam import FetchErrorSummary, FetchSuccessSummary
from app.schemas.online_runtime import LegadoRuntimeCode
from app.services.online.detector_adapter_skeleton import (
    prepare_detector_adapter_input,
    prepare_detector_adapter_output_noop,
)
from app.services.online.detector_skeleton import classify_detector_input
from app.services.online.fetch_service import FetchServiceError, RawFetchResponse
from app.services.online.live_seam_skeleton import (
    build_error_summary_from_stub,
    build_success_summary_from_stub,
    coerce_fetch_outcome_summary,
)


HTTP_STATUS_PATTERN = re.compile(r"status (\d{3})")
BODY_PREVIEW_LIMIT = 4096


def observe_live_entry_from_success_response(
    *,
    stage: str,
    expected_response_type: str,
    raw_response: RawFetchResponse,
) -> DetectorAdapterOutput:
    summary = build_success_summary_from_stub(
        {
            "stage": stage,
            "expected_response_type": expected_response_type,
            "requested_url": raw_response.requested_url,
            "fetch_outcome_kind": "success",
            "final_url": raw_response.final_url,
            "status_code": raw_response.status_code,
            "content_type": raw_response.content_type,
            "redirected": raw_response.final_url != raw_response.requested_url,
            "body_text_preview": _truncate_body_preview(raw_response.text),
            "body_text_length": len(raw_response.text),
        }
    )
    return observe_live_entry_from_summary(summary)


def observe_live_entry_from_fetch_error(
    *,
    stage: str,
    expected_response_type: str,
    requested_url: str,
    error: FetchServiceError,
) -> DetectorAdapterOutput:
    summary_payload = {
        "stage": stage,
        "expected_response_type": expected_response_type,
        "requested_url": requested_url,
    }
    summary_payload.update(_infer_fetch_error_summary_fields(error))
    summary = build_error_summary_from_stub(summary_payload)
    return observe_live_entry_from_summary(summary)


def observe_live_entry_from_summary(
    summary_or_stub: FetchSuccessSummary | FetchErrorSummary | Mapping[str, Any],
) -> DetectorAdapterOutput:
    summary = _coerce_summary(summary_or_stub)
    adapter_input = prepare_detector_adapter_input(summary)
    detector_input = _build_detector_input(summary)
    if detector_input is None:
        return prepare_detector_adapter_output_noop(adapter_input)

    detector_result = classify_detector_input(detector_input)
    return DetectorAdapterOutput.model_validate(
        {
            "outcome": DetectorAdapterOutcome.DETECTOR_RESULT_ATTACHED,
            "adapter_input": adapter_input,
            "detector_input": detector_input,
            "detector_result": detector_result,
        }
    )


def _coerce_summary(
    summary_or_stub: FetchSuccessSummary | FetchErrorSummary | Mapping[str, Any],
) -> FetchSuccessSummary | FetchErrorSummary:
    if isinstance(summary_or_stub, (FetchSuccessSummary, FetchErrorSummary)):
        return summary_or_stub
    if not isinstance(summary_or_stub, Mapping):
        raise TypeError("live-entry skeleton only accepts seam summaries or mapping-like stubs")
    return coerce_fetch_outcome_summary(dict(summary_or_stub))


def _build_detector_input(summary: FetchSuccessSummary | FetchErrorSummary) -> DetectorInput | None:
    required_values = (
        summary.final_url,
        summary.status_code,
        summary.content_type,
        summary.redirected,
        summary.body_text_preview,
        summary.body_text_length,
    )
    if any(value is None for value in required_values):
        return None

    return DetectorInput.model_validate(
        {
            "stage": summary.stage,
            "expected_response_type": summary.expected_response_type,
            "requested_url": summary.requested_url,
            "final_url": summary.final_url,
            "status_code": summary.status_code,
            "content_type": summary.content_type,
            "redirected": summary.redirected,
            "body_text_preview": summary.body_text_preview,
            "body_text_length": summary.body_text_length,
        }
    )


def _infer_fetch_error_summary_fields(error: FetchServiceError) -> dict[str, Any]:
    if error.code == LegadoRuntimeCode.REQUEST_TIMEOUT:
        return {
            "fetch_outcome_kind": "transport_error",
            "exception_kind": "timeout",
        }
    if error.code == LegadoRuntimeCode.RATE_LIMITED:
        return {
            "fetch_outcome_kind": "http_error",
            "status_code": 429,
        }

    message = str(error)
    status_match = HTTP_STATUS_PATTERN.search(message)
    if status_match is not None:
        return {
            "fetch_outcome_kind": "http_error",
            "status_code": int(status_match.group(1)),
        }
    if message.startswith("Request failed for "):
        return {
            "fetch_outcome_kind": "transport_error",
            "exception_kind": "request_error",
        }
    if message.startswith("Invalid runtime URL:"):
        return {
            "fetch_outcome_kind": "transport_error",
            "exception_kind": "invalid_url",
        }
    return {
        "fetch_outcome_kind": "transport_error",
        "exception_kind": "other",
    }


def _truncate_body_preview(text: str) -> str:
    if len(text) <= BODY_PREVIEW_LIMIT:
        return text
    return text[:BODY_PREVIEW_LIMIT]
