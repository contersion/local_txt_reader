import pytest

from app.schemas.online_runtime import RequestBodyMode, RequestRuntimeDescriptor
from app.services.online.request_profile_service import RequestProfileError, build_request_profile


def build_stage_request(**overrides):
    payload = {
        "method": "GET",
        "url": "https://example.com/search",
        "response_type": "html",
        "headers": {"User-Agent": "TXT-Reader-Test/1.0"},
        "query": {"q": "三体"},
        "body": {},
    }
    payload.update(overrides)
    return payload


def test_request_body_mode_enum_exposes_phase3b2_modes():
    assert [mode.value for mode in RequestBodyMode] == ["query", "form", "json", "raw"]


@pytest.mark.parametrize("body_mode", ["query", "form", RequestBodyMode.QUERY, RequestBodyMode.FORM])
def test_request_runtime_descriptor_accepts_query_and_form_modes(body_mode):
    descriptor = RequestRuntimeDescriptor.model_validate({"body_mode": body_mode})

    assert descriptor.body_mode == body_mode


def test_build_request_profile_without_runtime_descriptor_keeps_legacy_request_shape():
    stage_request = build_stage_request()

    profile = build_request_profile(stage_request=stage_request)

    assert profile.method == "GET"
    assert profile.url == "https://example.com/search"
    assert profile.response_type == "html"
    assert profile.headers == {"User-Agent": "TXT-Reader-Test/1.0"}
    assert profile.query == {"q": "三体"}
    assert profile.body == {}
    assert profile.cookies == {}


@pytest.mark.parametrize("body_mode", ["json", "raw", "xml"])
def test_build_request_profile_rejects_unsupported_request_body_mode(body_mode):
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(runtime={"body_mode": body_mode}),
        )

    assert exc_info.value.code.value == "LEGADO_UNSUPPORTED_REQUEST_BODY_MODE"


def test_build_request_profile_accepts_static_header_template_metadata():
    profile = build_request_profile(
        stage_request=build_stage_request(
            runtime={
                "header_template": {
                    "headers": {
                        "X-Trace": "static-value",
                        "X-Empty": "   ",
                    }
                }
            }
        )
    )

    assert profile.headers == {"User-Agent": "TXT-Reader-Test/1.0"}


@pytest.mark.parametrize(
    "header_name,header_value",
    [
        ("X-Trace", "{{token}}"),
        ("X-Trace", "javascript:alert(1)"),
    ],
)
def test_build_request_profile_rejects_invalid_header_template(header_name, header_value):
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(
                runtime={
                    "header_template": {
                        "headers": {
                            header_name: header_value,
                        }
                    }
                }
            )
        )

    assert exc_info.value.code.value == "LEGADO_INVALID_HEADER_TEMPLATE"


def test_build_request_profile_accepts_empty_signature_placeholder_spec():
    profile = build_request_profile(
        stage_request=build_stage_request(
            runtime={
                "signature_placeholders": {
                    "tokens": [],
                }
            }
        )
    )

    assert profile.url == "https://example.com/search"


def test_build_request_profile_rejects_signature_placeholder_flow():
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(
                runtime={
                    "signature_placeholders": {
                        "tokens": ["nonce", "sign"],
                    }
                }
            )
        )

    assert exc_info.value.code.value == "LEGADO_UNSUPPORTED_SIGNATURE_FLOW"


def test_build_request_profile_rejects_signature_like_header_template():
    with pytest.raises(RequestProfileError) as exc_info:
        build_request_profile(
            stage_request=build_stage_request(
                runtime={
                    "header_template": {
                        "headers": {
                            "X-Signature": "static-value",
                        }
                    }
                }
            )
        )

    assert exc_info.value.code.value == "LEGADO_UNSUPPORTED_SIGNATURE_FLOW"
