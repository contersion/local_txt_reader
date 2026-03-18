from dataclasses import dataclass

import httpx

from app.schemas.online_runtime import LegadoRuntimeCode


@dataclass(frozen=True, slots=True)
class ResponseGuardIssue:
    code: LegadoRuntimeCode
    message: str


def classify_transport_exception(exc: Exception, *, url: str) -> ResponseGuardIssue | None:
    if isinstance(exc, httpx.TimeoutException):
        return ResponseGuardIssue(
            code=LegadoRuntimeCode.REQUEST_TIMEOUT,
            message=f"Request timeout while fetching {url}",
        )
    return None


def classify_generic_response_issue(response: httpx.Response, *, url: str) -> ResponseGuardIssue | None:
    if response.status_code == 429:
        return ResponseGuardIssue(
            code=LegadoRuntimeCode.RATE_LIMITED,
            message=f"Remote request was rate limited with status 429 for {url}",
        )
    return None
