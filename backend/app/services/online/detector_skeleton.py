from app.schemas.online_detector import (
    DetectorCategory,
    DetectorClassificationResult,
    DetectorDeferredRequirementHint,
    DetectorInput,
    DetectorMatchStatus,
)
from app.schemas.online_runtime import LegadoRuntimeCode


CHALLENGE_BROWSER_CHECK_MARKERS = (
    "checking your browser",
    "browser check",
)
CHALLENGE_JS_COOKIE_MARKERS = (
    "enable javascript and cookies to continue",
    "enable javascript and cookies",
    "javascript and cookies to continue",
)
CHALLENGE_HUMAN_VERIFICATION_MARKERS = (
    "verify you are human",
    "human verification",
    "human verification required",
    "security check",
)
CHALLENGE_INTERACTIVE_CONTROL_MARKERS = (
    "captcha",
    "checkbox",
    "<form",
    "<button",
    "i am human",
)
CHALLENGE_PATH_HINT_MARKERS = (
    "/challenge",
    "/captcha",
    "/verify",
)

GATEWAY_ACCESS_DENIED_MARKERS = (
    "access denied",
)
GATEWAY_REQUEST_BLOCKED_MARKERS = (
    "request blocked",
)
GATEWAY_SECURITY_RULES_MARKERS = (
    "blocked by security rules",
    "security rules",
)
GATEWAY_FIREWALL_MARKERS = (
    "web application firewall",
    "firewall",
)
GATEWAY_SECURITY_SERVICE_MARKERS = (
    "security service",
)
GATEWAY_SECURITY_POLICY_MARKERS = (
    "forbidden by security policy",
    "security policy",
)
GATEWAY_PATH_HINT_MARKERS = (
    "/blocked",
    "/denied",
    "/challenge",
)
GATEWAY_STATUS_SUPPORT = {403, 503}


def classify_detector_input(detector_input: DetectorInput) -> DetectorClassificationResult:
    challenge_signals = _collect_challenge_signals(detector_input)
    if _is_challenge_candidate(challenge_signals):
        return DetectorClassificationResult.model_validate(
            {
                "category": DetectorCategory.CHALLENGE_CANDIDATE,
                "status": DetectorMatchStatus.CANDIDATE_MATCH,
                "matched_signals": challenge_signals,
                "evidence_snippets": _build_evidence_snippets(detector_input, challenge_signals),
                "recommended_error_code": LegadoRuntimeCode.ANTI_BOT_CHALLENGE,
                "deferred_requirement_hint": DetectorDeferredRequirementHint.NONE,
            }
        )

    gateway_signals = _collect_gateway_signals(detector_input)
    if _is_gateway_candidate(gateway_signals):
        return DetectorClassificationResult.model_validate(
            {
                "category": DetectorCategory.GATEWAY_CANDIDATE,
                "status": DetectorMatchStatus.CANDIDATE_MATCH,
                "matched_signals": gateway_signals,
                "evidence_snippets": _build_evidence_snippets(detector_input, gateway_signals),
                "recommended_error_code": LegadoRuntimeCode.BLOCKED_BY_ANTI_BOT_GATEWAY,
                "deferred_requirement_hint": DetectorDeferredRequirementHint.NONE,
            }
        )

    return DetectorClassificationResult.model_validate(
        {
            "category": DetectorCategory.NO_MATCH,
            "status": DetectorMatchStatus.NO_MATCH,
            "matched_signals": [],
            "evidence_snippets": [],
            "recommended_error_code": None,
            "deferred_requirement_hint": DetectorDeferredRequirementHint.NONE,
        }
    )


def _collect_challenge_signals(detector_input: DetectorInput) -> list[str]:
    text = detector_input.body_text_preview.lower()
    final_url = detector_input.final_url.lower()
    signals: list[str] = []

    if _contains_any(text, CHALLENGE_BROWSER_CHECK_MARKERS):
        signals.append("challenge_browser_check")
    if _contains_any(text, CHALLENGE_JS_COOKIE_MARKERS):
        signals.append("challenge_js_cookie_continue")
    if _contains_any(text, CHALLENGE_HUMAN_VERIFICATION_MARKERS):
        signals.append("challenge_human_verification")
    if _contains_any(text, CHALLENGE_INTERACTIVE_CONTROL_MARKERS):
        signals.append("challenge_interactive_control")
    if _contains_any(final_url, CHALLENGE_PATH_HINT_MARKERS):
        signals.append("challenge_path_hint")

    return signals


def _collect_gateway_signals(detector_input: DetectorInput) -> list[str]:
    text = detector_input.body_text_preview.lower()
    final_url = detector_input.final_url.lower()
    signals: list[str] = []

    if _contains_any(text, GATEWAY_ACCESS_DENIED_MARKERS):
        signals.append("gateway_access_denied")
    if _contains_any(text, GATEWAY_REQUEST_BLOCKED_MARKERS):
        signals.append("gateway_request_blocked")
    if _contains_any(text, GATEWAY_SECURITY_RULES_MARKERS):
        signals.append("gateway_security_rules")
    if _contains_any(text, GATEWAY_FIREWALL_MARKERS):
        signals.append("gateway_firewall_wording")
    if _contains_any(text, GATEWAY_SECURITY_SERVICE_MARKERS):
        signals.append("gateway_security_service")
    if _contains_any(text, GATEWAY_SECURITY_POLICY_MARKERS):
        signals.append("gateway_security_policy")
    if detector_input.status_code in GATEWAY_STATUS_SUPPORT:
        signals.append("gateway_status_support")
    if _contains_any(final_url, GATEWAY_PATH_HINT_MARKERS):
        signals.append("gateway_path_hint")

    return signals


def _is_challenge_candidate(signals: list[str]) -> bool:
    signal_set = set(signals)
    return (
        {"challenge_browser_check", "challenge_js_cookie_continue"} <= signal_set
        or {"challenge_human_verification", "challenge_interactive_control"} <= signal_set
        or {"challenge_browser_check", "challenge_path_hint"} <= signal_set
    )


def _is_gateway_candidate(signals: list[str]) -> bool:
    signal_set = set(signals)
    return (
        ("gateway_access_denied" in signal_set or "gateway_request_blocked" in signal_set)
        and (
            "gateway_security_rules" in signal_set
            or "gateway_security_service" in signal_set
            or "gateway_security_policy" in signal_set
            or "gateway_firewall_wording" in signal_set
        )
    ) or (
        ("gateway_security_service" in signal_set or "gateway_firewall_wording" in signal_set)
        and "gateway_status_support" in signal_set
        and (
            "gateway_path_hint" in signal_set
            or "gateway_access_denied" in signal_set
            or "gateway_request_blocked" in signal_set
        )
    )


def _build_evidence_snippets(detector_input: DetectorInput, signals: list[str]) -> list[str]:
    text = detector_input.body_text_preview.strip()
    if not text:
        return []
    snippet = text[:200]
    if len(text) > 200:
        snippet += "..."
    return [f"{','.join(signals)} :: {snippet}"]


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)
