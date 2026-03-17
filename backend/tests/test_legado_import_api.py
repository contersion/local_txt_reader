import json
from contextlib import contextmanager

import httpx
from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application


# Sample S1: minimal valid whitelist source.
VALID_LEGADO_SOURCE = {
    "bookSourceName": "Legado CSS/XPath/JSONPath/Regex Source",
    "bookSourceComment": "Strict whitelist import source",
    "bookSourceUrl": "https://example.com",
    "enabled": True,
    "searchUrl": '/search?q={{key}}&page={{page}},{"method":"GET","headers":{"User-Agent":"Legado-Test/1.0"}}',
    "ruleSearch": {
        "bookList": "css:.result-item",
        "name": "css:a.title@text",
        "bookUrl": "css:a.title@href",
        "author": "css:.author@text",
        "intro": "css:.intro@text",
        "coverUrl": "css:img.cover@src",
        "bookId": "css:a.title@data-book-id",
    },
    "ruleBookInfo": {
        "name": "jsonpath:$.book.title",
        "author": "jsonpath:$.book.author",
        "intro": "jsonpath:$.book.description",
        "coverUrl": "jsonpath:$.book.cover",
        "tocUrl": "jsonpath:$.book.catalog_url",
    },
    "ruleToc": {
        "chapterList": "xpath://li[@class='chapter-item']",
        "chapterName": "xpath:./a/text()",
        "chapterUrl": "xpath:./a/@href",
    },
    "ruleContent": {
        "content": 'regex:<div id="content">([\\s\\S]+?)</div>##1',
    },
}

# Sample S2: alias-heavy valid source plus CSS/JSoup normalization cases.
VALID_LEGADO_ALIAS_SOURCE = {
    "bookSourceName": "Legado Alias Source",
    "bookSourceComment": "Alias-heavy whitelist source",
    "bookSourceUrl": "https://example.com",
    "enabled": True,
    "searchUrl": '/search?q={{key}}&page={{page}},{"method":"post","header":{"User-Agent":"Legado-Test/2.0"},"body":"key={{key}}&page={{page}}"}',
    "ruleSearch": {
        "list": "jsoup:.result-item",
        "bookName": ".result-item a.title@text",
        "url": ".result-item a.title@href",
        "author": ".result-item .author@text",
        "desc": ".result-item .intro@text",
        "cover": ".result-item img.cover@src",
        "id": ".result-item a.title@data-book-id",
    },
    "ruleBookInfo": {
        "bookName": "json:$.book.title",
        "author": "json:$.book.author",
        "description": "json:$.book.description",
        "cover": "json:$.book.cover",
        "catalogUrl": "json:$.book.catalog_url",
    },
    "ruleToc": {
        "list": "xpath://li[@class='chapter-item']",
        "name": "xpath:./a/text()",
        "url": "xpath:./a/@href",
    },
    "ruleContent": {
        "text": "jsoup:#content@html",
    },
}

# Sample S12: source-level ignored metadata fields that are explicitly whitelisted.
VALID_LEGADO_SOURCE_LEVEL_IGNORED_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "bookSourceType": 0,
    "lastUpdateTime": "2026-03-17 12:00:00",
    "respondTime": 123,
}

# Sample S13: absolute search URL should remain valid in the importer.
VALID_LEGADO_ABSOLUTE_URL_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "searchUrl": 'https://search.example.com/search?q={{key}}&page={{page}},{"method":"GET"}',
}

# Sample S14: unsupported parser prefix should hard fail.
INVALID_LEGADO_UNSUPPORTED_PARSER_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "ruleSearch": {
        **VALID_LEGADO_SOURCE["ruleSearch"],
        "bookList": "jq:.result-item",
    },
}

# Sample S15: complex HTML DSL should hard fail instead of being treated as a valid attr extraction.
INVALID_LEGADO_COMPLEX_HTML_DSL_SOURCE = {
    **VALID_LEGADO_ALIAS_SOURCE,
    "ruleContent": {
        "text": "jsoup:#content@css:.inner",
    },
}

# Sample S16: search-stage ignored metadata fields.
VALID_LEGADO_SEARCH_STAGE_IGNORED_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "ruleSearch": {
        **VALID_LEGADO_SOURCE["ruleSearch"],
        "kind": "sci-fi",
        "lastChapter": "Chapter 99",
        "wordCount": "100000",
        "updateTime": "2026-03-17",
    },
}

# Sample S17: detail-stage ignored metadata fields.
VALID_LEGADO_DETAIL_STAGE_IGNORED_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "ruleBookInfo": {
        **VALID_LEGADO_SOURCE["ruleBookInfo"],
        "kind": "sci-fi",
        "lastChapter": "Chapter 99",
        "wordCount": "100000",
        "updateTime": "2026-03-17",
    },
}

# Sample S18: explicit bridge from search.detail_url -> detail.request.url placeholder.
VALID_LEGADO_DETAIL_URL_BRIDGE_SOURCE = {
    **VALID_LEGADO_SOURCE,
}

# Sample S19: explicit bridge from detail.catalog_url -> catalog.request.url placeholder.
VALID_LEGADO_CATALOG_URL_BRIDGE_SOURCE = {
    **VALID_LEGADO_SOURCE,
}

# Sample S20: explicit bridge from catalog.chapter_url -> content.request.url placeholder.
VALID_LEGADO_CHAPTER_URL_BRIDGE_SOURCE = {
    **VALID_LEGADO_SOURCE,
}

# Sample S21: Authorization headers are outside the Phase 2 whitelist.
INVALID_LEGADO_AUTHORIZATION_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "header": {
        "Authorization": "Bearer secret-token",
    },
}

# Sample S22: dynamic variables stay outside the Phase 2 whitelist.
INVALID_LEGADO_DYNAMIC_VARIABLE_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "variables": {
        "token": "abc123",
    },
}

# Sample S23: condition DSL stays outside the Phase 2 whitelist.
INVALID_LEGADO_CONDITION_DSL_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "conditions": {
        "if": "userLoggedIn",
    },
}

# Sample S24: only GET/POST methods are supported.
INVALID_LEGADO_UNSUPPORTED_METHOD_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "searchUrl": '/search?q={{key}}&page={{page}},{"method":"PUT"}',
}

# Sample S25: multi-request chains stay outside the Phase 2 whitelist.
INVALID_LEGADO_MULTI_REQUEST_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "requests": [
        {
            "url": "/search?q={{key}}",
        }
    ],
}

# Sample S26: script-style dynamic requests stay outside the Phase 2 whitelist.
INVALID_LEGADO_DYNAMIC_REQUEST_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "searchUrl": "@get:https://example.com/search?q={{key}}",
}

# Sample S27: invalid base URLs fail during canonical validation.
INVALID_LEGADO_INVALID_URL_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "bookSourceUrl": "ftp://example.com",
}

# Sample S28: required top-level stage definitions cannot be omitted.
INVALID_LEGADO_REQUIRED_FIELD_MISSING_SOURCE = {
    key: value for key, value in VALID_LEGADO_SOURCE.items() if key != "ruleContent"
}

# Sample S29: malformed stage structures fail as mapping errors.
INVALID_LEGADO_MAPPING_FAILED_SOURCE = {
    **VALID_LEGADO_SOURCE,
    "ruleSearch": "not-an-object",
}


@contextmanager
def authenticated_client(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "default_admin_username", "admin")
    monkeypatch.setattr(settings, "default_admin_password", "admin123")
    monkeypatch.setattr(settings, "secret_key", "test-secret-key")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    with TestClient(create_application()) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        yield client


def build_validate_payload(source: dict | None = None) -> dict:
    return {"source": source or VALID_LEGADO_SOURCE}


def stub_httpx_request(monkeypatch, responses_by_url: dict[str, httpx.Response | Exception]):
    def _request(method: str, url: str, **kwargs):
        response_or_error = responses_by_url[url]
        if isinstance(response_or_error, Exception):
            raise response_or_error
        return response_or_error

    monkeypatch.setattr(httpx, "request", _request)


def build_response(
    method: str,
    url: str,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
    content: bytes | str = b"",
) -> httpx.Response:
    request = httpx.Request(method, url)
    if isinstance(content, str):
        content = content.encode("utf-8")
    return httpx.Response(status_code=status_code, headers=headers, content=content, request=request)


# Success samples
# S1
def test_validate_legado_import_accepts_supported_whitelist_source(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    assert payload["errors"] == []
    assert payload["mapped_source"]["name"] == VALID_LEGADO_SOURCE["bookSourceName"]
    assert payload["mapped_source"]["definition"]["search"]["list_selector"]["parser"] == "css"
    assert payload["mapped_source"]["definition"]["detail"]["fields"]["title"]["parser"] == "jsonpath"
    assert payload["mapped_source"]["definition"]["catalog"]["list_selector"]["parser"] == "xpath"
    assert payload["mapped_source"]["definition"]["content"]["fields"]["content"]["parser"] == "regex"
    assert payload["mapped_source"]["definition"]["content"]["fields"]["content"]["regex_group"] == 1


# S1
def test_import_legado_source_persists_online_source(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import", json=build_validate_payload())
        assert response.status_code == 201
        payload = response.json()

        list_response = client.get("/api/online-sources")

    assert payload["is_valid"] is True
    assert payload["source_id"] is not None
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == VALID_LEGADO_SOURCE["bookSourceName"]


# Reject samples
# S4
def test_validate_legado_import_rejects_js(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "ruleContent": {
            "content": "@js:result",
        },
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_JS"}
    issue = payload["errors"][0]
    assert issue["error_code"] == "LEGADO_UNSUPPORTED_JS"
    assert issue["severity"] == "error"
    assert issue["source_path"] == "ruleContent.content"
    assert issue["stage"] == "content"
    assert issue["field_name"] == "content"
    assert issue["raw_value"] == "@js:result"
    assert issue["normalized_value"] is None


# S5
def test_validate_legado_import_rejects_cookie_and_login_state(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "loginUrl": "https://example.com/login",
        "header": {
            "Cookie": "sid=1",
        },
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    error_codes = {issue["code"] for issue in payload["errors"]}
    assert "LEGADO_UNSUPPORTED_COOKIE" in error_codes
    assert "LEGADO_UNSUPPORTED_LOGIN_STATE" in error_codes
    cookie_issue = next(issue for issue in payload["errors"] if issue["code"] == "LEGADO_UNSUPPORTED_COOKIE")
    assert cookie_issue["severity"] == "error"
    assert cookie_issue["source_path"] == "header.Cookie"
    assert cookie_issue["stage"] == "source"
    assert cookie_issue["field_name"] == "Cookie"
    assert cookie_issue["raw_value"] == "sid=1"


# S21
def test_validate_legado_import_rejects_authorization_header(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_AUTHORIZATION_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    authorization_issues = [issue for issue in payload["errors"] if issue["code"] == "LEGADO_UNSUPPORTED_AUTHORIZATION"]
    assert len(authorization_issues) == 1
    issue = authorization_issues[0]
    assert issue["source_path"] == "header.Authorization"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "Authorization"
    assert issue["raw_value"] == "Bearer secret-token"


# S6
def test_validate_legado_import_rejects_webview_and_proxy(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "webView": True,
        "proxy": "http://127.0.0.1:8888",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    error_codes = {issue["code"] for issue in payload["errors"]}
    assert "LEGADO_UNSUPPORTED_WEBVIEW" in error_codes
    assert "LEGADO_UNSUPPORTED_PROXY" in error_codes
    webview_issue = next(issue for issue in payload["errors"] if issue["code"] == "LEGADO_UNSUPPORTED_WEBVIEW")
    assert webview_issue["source_path"] == "webView"
    assert webview_issue["stage"] == "source"
    assert webview_issue["field_name"] == "webView"
    assert webview_issue["raw_value"] is True


# S7
def test_validate_legado_import_rejects_charset_override(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "charset": "gbk",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_CHARSET_OVERRIDE"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "charset"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "charset"
    assert issue["raw_value"] == "gbk"


# S22
def test_validate_legado_import_rejects_dynamic_variable_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_DYNAMIC_VARIABLE_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "variables"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "variables"
    assert issue["raw_value"] == {"token": "abc123"}


# S23
def test_validate_legado_import_rejects_condition_dsl(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_CONDITION_DSL_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_CONDITION_DSL"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "conditions"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "conditions"
    assert issue["raw_value"] == {"if": "userLoggedIn"}


# S24
def test_validate_legado_import_rejects_unsupported_method(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_UNSUPPORTED_METHOD_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_METHOD"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "searchUrl.method"
    assert issue["raw_value"] is None


# S25
def test_validate_legado_import_rejects_multi_request_structures(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_MULTI_REQUEST_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    multi_request_issues = [issue for issue in payload["errors"] if issue["code"] == "LEGADO_UNSUPPORTED_MULTI_REQUEST"]
    assert len(multi_request_issues) == 1
    issue = multi_request_issues[0]
    assert issue["source_path"] == "requests"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "requests"
    assert issue["raw_value"] == [{"url": "/search?q={{key}}"}]


# S26
def test_validate_legado_import_rejects_dynamic_request_patterns(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_DYNAMIC_REQUEST_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_DYNAMIC_REQUEST"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "searchUrl"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "searchUrl"
    assert issue["raw_value"] == "@get:https://example.com/search?q={{key}}"


# S27
def test_validate_legado_import_rejects_invalid_base_url(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_INVALID_URL_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_INVALID_URL"}
    issue = payload["errors"][0]
    assert issue["source_path"] is None
    assert "base_url" in issue["message"]


# S28
def test_validate_legado_import_rejects_missing_required_stage_definition(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_REQUIRED_FIELD_MISSING_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_REQUIRED_FIELD_MISSING"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "ruleContent"
    assert issue["stage"] == "content"
    assert issue["field_name"] == "ruleContent"


# S29
def test_validate_legado_import_rejects_invalid_stage_shape(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_MAPPING_FAILED_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_MAPPING_FAILED"}
    issue = payload["errors"][0]
    assert issue["source_path"] == "ruleSearch"
    assert issue["stage"] == "search"
    assert issue["field_name"] == "ruleSearch"
    assert issue["raw_value"] == "not-an-object"


# S10
def test_validate_legado_import_rejects_unknown_placeholder(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "searchUrl": "/search?q={{secret}}",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_PLACEHOLDER"}


# Warning samples
# S3
def test_validate_legado_import_warns_and_ignores_display_fields(monkeypatch, tmp_path):
    warning_source = {
        **VALID_LEGADO_SOURCE,
        "bookSourceGroup": "Group A",
        "customOrder": 10,
        "weight": 3,
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(warning_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    assert sorted(payload["ignored_fields"]) == ["bookSourceGroup", "customOrder", "weight"]
    warning_codes = {issue["code"] for issue in payload["warnings"]}
    assert warning_codes == {"LEGADO_IGNORED_FIELD"}
    issue = next(issue for issue in payload["warnings"] if issue["source_path"] == "bookSourceGroup")
    assert issue["severity"] == "warning"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "bookSourceGroup"
    assert issue["raw_value"] == "Group A"


# S12
def test_validate_legado_import_warns_and_ignores_source_level_metadata_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_SOURCE_LEVEL_IGNORED_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    warning_paths = {issue["source_path"] for issue in payload["warnings"]}
    assert {"bookSourceType", "lastUpdateTime", "respondTime"} <= warning_paths
    assert {"bookSourceType", "lastUpdateTime", "respondTime"} <= set(payload["ignored_fields"])


# S9
def test_validate_legado_import_unknown_display_like_field_is_hard_error(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "themeColor": "#ffffff",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert payload["warnings"] == []
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_FIELD"}
    assert payload["unsupported_fields"] == ["themeColor"]


# Success samples with alias/static normalization coverage
# S2 + S11
def test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(VALID_LEGADO_ALIAS_SOURCE))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    mapped_source = payload["mapped_source"]
    assert mapped_source["definition"]["search"]["request"]["method"] == "POST"
    assert mapped_source["definition"]["search"]["request"]["headers"]["User-Agent"] == "Legado-Test/2.0"
    assert mapped_source["definition"]["search"]["request"]["body"] == {"key": "{{keyword}}", "page": "{{page}}"}
    assert mapped_source["definition"]["search"]["list_selector"]["parser"] == "css"
    assert mapped_source["definition"]["search"]["fields"]["title"]["expr"] == ".result-item a.title"
    assert mapped_source["definition"]["search"]["fields"]["title"]["attr"] is None
    assert mapped_source["definition"]["search"]["fields"]["detail_url"]["attr"] == "href"
    assert mapped_source["definition"]["search"]["fields"]["cover_url"]["attr"] == "src"
    assert mapped_source["definition"]["detail"]["fields"]["description"]["parser"] == "jsonpath"
    assert mapped_source["definition"]["catalog"]["fields"]["chapter_title"]["parser"] == "xpath"
    assert mapped_source["definition"]["content"]["fields"]["content"]["parser"] == "css"
    assert mapped_source["definition"]["content"]["fields"]["content"]["expr"] == "#content"
    html_issue = next(issue for issue in payload["warnings"] if issue["code"] == "LEGADO_CSS_HTML_NORMALIZED")
    assert html_issue["error_code"] == "LEGADO_CSS_HTML_NORMALIZED"
    assert html_issue["severity"] == "warning"
    assert html_issue["source_path"] == "ruleContent.text"
    assert html_issue["stage"] == "content"
    assert html_issue["field_name"] == "text"
    assert html_issue["raw_value"] == "jsoup:#content@html"
    assert html_issue["normalized_value"] == {"parser": "css", "expr": "#content"}


# S13
def test_validate_legado_import_accepts_absolute_search_url(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_ABSOLUTE_URL_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    assert payload["mapped_source"]["definition"]["search"]["request"]["url"] == "https://search.example.com/search?q={{keyword}}&page={{page}}"


# S18
def test_validate_legado_import_exposes_detail_url_bridge_placeholder(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_DETAIL_URL_BRIDGE_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    mapped_source = payload["mapped_source"]
    assert mapped_source["definition"]["search"]["fields"]["detail_url"]["parser"] == "css"
    assert mapped_source["definition"]["detail"]["request"]["url"] == "{{detail_url}}"


# S19
def test_validate_legado_import_exposes_catalog_url_bridge_placeholder(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_CATALOG_URL_BRIDGE_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    mapped_source = payload["mapped_source"]
    assert mapped_source["definition"]["detail"]["fields"]["catalog_url"]["parser"] == "jsonpath"
    assert mapped_source["definition"]["catalog"]["request"]["url"] == "{{catalog_url}}"


# S20
def test_validate_legado_import_exposes_chapter_url_bridge_placeholder(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_CHAPTER_URL_BRIDGE_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    mapped_source = payload["mapped_source"]
    assert mapped_source["definition"]["catalog"]["fields"]["chapter_url"]["parser"] == "xpath"
    assert mapped_source["definition"]["content"]["request"]["url"] == "{{chapter_url}}"


# S8
def test_validate_legado_import_rejects_replace_dsl(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "replaceRule": "##广告##",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_REPLACE_DSL"}


# S14
def test_validate_legado_import_rejects_unsupported_parser_prefix(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_UNSUPPORTED_PARSER_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_PARSER"}


# S15
def test_validate_legado_import_rejects_complex_html_dsl(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(INVALID_LEGADO_COMPLEX_HTML_DSL_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is False
    assert {issue["code"] for issue in payload["errors"]} == {"LEGADO_UNSUPPORTED_PARSER"}


# S9
def test_validate_legado_import_unknown_field_returns_precise_location(monkeypatch, tmp_path):
    invalid_source = {
        **VALID_LEGADO_SOURCE,
        "themeColor": "#ffffff",
    }

    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/online-sources/import/validate", json=build_validate_payload(invalid_source))

    assert response.status_code == 200
    payload = response.json()
    issue = payload["errors"][0]
    assert issue["code"] == "LEGADO_UNSUPPORTED_FIELD"
    assert issue["source_path"] == "themeColor"
    assert issue["stage"] == "source"
    assert issue["field_name"] == "themeColor"
    assert issue["raw_value"] == "#ffffff"


# S16
def test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_SEARCH_STAGE_IGNORED_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    warning_paths = {issue["source_path"] for issue in payload["warnings"]}
    assert {
        "ruleSearch.kind",
        "ruleSearch.lastChapter",
        "ruleSearch.wordCount",
        "ruleSearch.updateTime",
    } <= warning_paths


# S17
def test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/online-sources/import/validate",
            json=build_validate_payload(VALID_LEGADO_DETAIL_STAGE_IGNORED_SOURCE),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    warning_paths = {issue["source_path"] for issue in payload["warnings"]}
    assert {
        "ruleBookInfo.kind",
        "ruleBookInfo.lastChapter",
        "ruleBookInfo.wordCount",
        "ruleBookInfo.updateTime",
    } <= warning_paths


# Post-import execution compatibility samples
# S1
def test_imported_legado_source_can_run_existing_discovery_search(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        import_response = client.post("/api/online-sources/import", json=build_validate_payload())
        assert import_response.status_code == 201
        source_id = import_response.json()["source_id"]

        search_url = "https://example.com/search?q=three-body&page=1"
        stub_httpx_request(
            monkeypatch,
            {
                search_url: build_response(
                    "GET",
                    search_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div class="result-item">
                        <a class="title" href="/books/1" data-book-id="book-1">Three Body</a>
                        <span class="author">Liu Cixin</span>
                        <span class="intro">Sci-fi epic</span>
                        <img class="cover" src="/covers/1.jpg" />
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        discovery_response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source_id, "keyword": "three-body", "page": 1},
        )

    assert discovery_response.status_code == 200
    payload = discovery_response.json()
    assert payload["items"][0]["title"] == "Three Body"
    assert payload["items"][0]["detail_url"] == "https://example.com/books/1"


# S2
def test_imported_alias_source_can_run_existing_discovery_search(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        import_response = client.post("/api/online-sources/import", json=build_validate_payload(VALID_LEGADO_ALIAS_SOURCE))
        assert import_response.status_code == 201
        source_id = import_response.json()["source_id"]

        search_url = "https://example.com/search?q=three-body&page=1"
        stub_httpx_request(
            monkeypatch,
            {
                search_url: build_response(
                    "POST",
                    search_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div class="result-item">
                        <a class="title" href="/books/2" data-book-id="book-2">The Dark Forest</a>
                        <span class="author">Liu Cixin</span>
                        <span class="intro">Second novel</span>
                        <img class="cover" src="/covers/2.jpg" />
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        discovery_response = client.post(
            "/api/online-discovery/search",
            json={"source_id": source_id, "keyword": "three-body", "page": 1},
        )

    assert discovery_response.status_code == 200
    payload = discovery_response.json()
    assert payload["items"][0]["title"] == "The Dark Forest"
    assert payload["items"][0]["detail_url"] == "https://example.com/books/2"


def test_imported_legado_source_can_run_detail_catalog_and_chapter_chain(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        import_response = client.post("/api/online-sources/import", json=build_validate_payload())
        assert import_response.status_code == 201
        source_id = import_response.json()["source_id"]

        list_response = client.get("/api/online-sources")
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [source_id]

        detail_url = "https://example.com/books/1"
        catalog_url = "https://example.com/books/1/catalog"
        chapter_url = "https://example.com/books/1/ch1"
        stub_httpx_request(
            monkeypatch,
            {
                detail_url: build_response(
                    "GET",
                    detail_url,
                    headers={"content-type": "application/json"},
                    content=json.dumps(
                        {
                            "book": {
                                "title": "Three Body",
                                "author": "Liu Cixin",
                                "description": "Sci-fi epic",
                                "cover": "https://example.com/covers/1.jpg",
                                "catalog_url": catalog_url,
                            }
                        }
                    ),
                ),
                catalog_url: build_response(
                    "GET",
                    catalog_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <ul>
                        <li class="chapter-item"><a href="/books/1/ch1">Chapter 1</a></li>
                        <li class="chapter-item"><a href="/books/1/ch2">Chapter 2</a></li>
                      </ul>
                    </body></html>
                    """,
                ),
                chapter_url: build_response(
                    "GET",
                    chapter_url,
                    headers={"content-type": "text/html; charset=utf-8"},
                    content="""
                    <html><body>
                      <div id="content">
                        Paragraph 1<br/>
                        Paragraph 2
                      </div>
                    </body></html>
                    """,
                ),
            },
        )

        detail_response = client.post(
            "/api/online-discovery/detail",
            json={"source_id": source_id, "detail_url": detail_url, "remote_book_id": "book-1"},
        )
        catalog_response = client.post(
            "/api/online-discovery/catalog",
            json={"source_id": source_id, "catalog_url": catalog_url},
        )
        chapter_response = client.post(
            "/api/online-discovery/chapter",
            json={
                "source_id": source_id,
                "chapter_url": chapter_url,
                "chapter_index": 0,
                "chapter_title": "Chapter 1",
            },
        )

    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Three Body"
    assert catalog_response.status_code == 200
    assert catalog_response.json()["items"][0]["source_locator"]["url"] == chapter_url
    assert chapter_response.status_code == 200
    assert chapter_response.json()["chapter_title"] == "Chapter 1"
    assert "Paragraph 1" in chapter_response.json()["content"]
