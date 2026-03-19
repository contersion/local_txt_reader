from collections.abc import Mapping
from typing import Any

import httpx

from app.schemas.online_live_seam import (
    FetchErrorSummary,
    FetchOutcomeKind,
    FetchSuccessSummary,
)


def build_success_summary_from_stub(stub: Mapping[str, Any] | dict[str, Any]) -> FetchSuccessSummary:
    payload = _coerce_stub_mapping(stub)
    return FetchSuccessSummary.model_validate(payload)


def build_error_summary_from_stub(stub: Mapping[str, Any] | dict[str, Any]) -> FetchErrorSummary:
    payload = _coerce_stub_mapping(stub)
    return FetchErrorSummary.model_validate(payload)


def coerce_fetch_outcome_summary(stub: Mapping[str, Any] | dict[str, Any]) -> FetchSuccessSummary | FetchErrorSummary:
    payload = _coerce_stub_mapping(stub)
    outcome_kind = FetchOutcomeKind(payload["fetch_outcome_kind"])
    if outcome_kind == FetchOutcomeKind.SUCCESS:
        return FetchSuccessSummary.model_validate(payload)
    return FetchErrorSummary.model_validate(payload)


def _coerce_stub_mapping(stub: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(stub, httpx.Response) or isinstance(stub, BaseException):
        raise TypeError("live seam skeleton helpers only accept internal stub mappings")
    if not isinstance(stub, Mapping):
        raise TypeError("live seam skeleton helpers only accept mapping-like stubs")
    return dict(stub)
