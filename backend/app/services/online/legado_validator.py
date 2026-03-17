import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.legado_import import LegadoImportCode, LegadoImportIssue, LegadoIssueSeverity
from app.services.online.source_validator import OnlineSourceValidationError, validate_phase1_source_definition


SUPPORTED_TOP_LEVEL_FIELDS = {
    "bookSourceName",
    "bookSourceComment",
    "bookSourceUrl",
    "enabled",
    "header",
    "searchUrl",
    "ruleSearch",
    "ruleBookInfo",
    "ruleToc",
    "ruleContent",
}
IGNORED_TOP_LEVEL_FIELDS = {
    "bookSourceGroup",
    "bookSourceType",
    "customOrder",
    "weight",
    "lastUpdateTime",
    "respondTime",
}
# Only explicitly listed display/meta fields are allowed to degrade to warning+ignore.
# Any unknown field outside this allowlist must stay a hard error in Phase 2.
STAGE_SUPPORTED_FIELDS = {
    "ruleSearch": {"bookList", "list", "name", "bookName", "bookUrl", "url", "author", "intro", "desc", "description", "coverUrl", "cover", "bookId", "id"},
    "ruleBookInfo": {"name", "bookName", "author", "intro", "desc", "description", "coverUrl", "cover", "tocUrl", "catalogUrl", "chapterUrl"},
    "ruleToc": {"chapterList", "list", "chapterName", "name", "chapterUrl", "url"},
    "ruleContent": {"content", "text", "body"},
}
STAGE_IGNORED_FIELDS = {
    "ruleSearch": {"kind", "lastChapter", "wordCount", "updateTime"},
    "ruleBookInfo": {"kind", "lastChapter", "wordCount", "updateTime"},
    "ruleToc": set(),
    "ruleContent": set(),
}
FORBIDDEN_FIELD_CODES = {
    "charset": LegadoImportCode.UNSUPPORTED_CHARSET_OVERRIDE,
    "cookie": LegadoImportCode.UNSUPPORTED_COOKIE,
    "cookies": LegadoImportCode.UNSUPPORTED_COOKIE,
    "authorization": LegadoImportCode.UNSUPPORTED_AUTHORIZATION,
    "login": LegadoImportCode.UNSUPPORTED_LOGIN_STATE,
    "loginurl": LegadoImportCode.UNSUPPORTED_LOGIN_STATE,
    "session": LegadoImportCode.UNSUPPORTED_LOGIN_STATE,
    "token": LegadoImportCode.UNSUPPORTED_LOGIN_STATE,
    "webview": LegadoImportCode.UNSUPPORTED_WEBVIEW,
    "proxy": LegadoImportCode.UNSUPPORTED_PROXY,
    "proxyurl": LegadoImportCode.UNSUPPORTED_PROXY,
    "variables": LegadoImportCode.UNSUPPORTED_DYNAMIC_VARIABLE,
    "variable": LegadoImportCode.UNSUPPORTED_DYNAMIC_VARIABLE,
    "conditions": LegadoImportCode.UNSUPPORTED_CONDITION_DSL,
    "condition": LegadoImportCode.UNSUPPORTED_CONDITION_DSL,
    "replace": LegadoImportCode.UNSUPPORTED_REPLACE_DSL,
    "replacerule": LegadoImportCode.UNSUPPORTED_REPLACE_DSL,
    "replaceregex": LegadoImportCode.UNSUPPORTED_REPLACE_DSL,
    "replacelist": LegadoImportCode.UNSUPPORTED_REPLACE_DSL,
    "js": LegadoImportCode.UNSUPPORTED_JS,
    "script": LegadoImportCode.UNSUPPORTED_JS,
    "scripts": LegadoImportCode.UNSUPPORTED_JS,
    "requests": LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
    "steps": LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
    "pipeline": LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
    "nexttocurl": LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
    "nextcontenturl": LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
}
FORBIDDEN_STRING_PATTERNS = {
    "@js:": LegadoImportCode.UNSUPPORTED_JS,
    "<js": LegadoImportCode.UNSUPPORTED_JS,
    "</js": LegadoImportCode.UNSUPPORTED_JS,
    "javascript:": LegadoImportCode.UNSUPPORTED_JS,
    "eval(": LegadoImportCode.UNSUPPORTED_JS,
    "function(": LegadoImportCode.UNSUPPORTED_JS,
    "=>": LegadoImportCode.UNSUPPORTED_JS,
    "@put": LegadoImportCode.UNSUPPORTED_DYNAMIC_REQUEST,
    "@get": LegadoImportCode.UNSUPPORTED_DYNAMIC_REQUEST,
    "java.put": LegadoImportCode.UNSUPPORTED_DYNAMIC_REQUEST,
    "java.get": LegadoImportCode.UNSUPPORTED_DYNAMIC_REQUEST,
}
PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
ALLOWED_RAW_PLACEHOLDERS = {"key", "page"}


@dataclass
class LegadoValidationReport:
    errors: list[LegadoImportIssue] = field(default_factory=list)
    warnings: list[LegadoImportIssue] = field(default_factory=list)
    ignored_fields: list[str] = field(default_factory=list)
    unsupported_fields: list[str] = field(default_factory=list)
    _seen: set[tuple[str, str | None, str]] = field(default_factory=set)

    def add_error(
        self,
        code: LegadoImportCode,
        message: str,
        field_path: str | None = None,
        *,
        raw_value: Any | None = None,
        normalized_value: Any | None = None,
        stage: str | None = None,
        field_name: str | None = None,
    ) -> None:
        self._add_issue(
            self.errors,
            code,
            message,
            field_path,
            severity=LegadoIssueSeverity.ERROR,
            raw_value=raw_value,
            normalized_value=normalized_value,
            stage=stage,
            field_name=field_name,
        )
        if field_path and field_path not in self.unsupported_fields:
            self.unsupported_fields.append(field_path)

    def add_warning(
        self,
        code: LegadoImportCode,
        message: str,
        field_path: str | None = None,
        *,
        raw_value: Any | None = None,
        normalized_value: Any | None = None,
        stage: str | None = None,
        field_name: str | None = None,
    ) -> None:
        self._add_issue(
            self.warnings,
            code,
            message,
            field_path,
            severity=LegadoIssueSeverity.WARNING,
            raw_value=raw_value,
            normalized_value=normalized_value,
            stage=stage,
            field_name=field_name,
        )
        if field_path and field_path not in self.ignored_fields:
            self.ignored_fields.append(field_path)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def _add_issue(
        self,
        bucket: list[LegadoImportIssue],
        code: LegadoImportCode,
        message: str,
        field_path: str | None,
        *,
        severity: LegadoIssueSeverity,
        raw_value: Any | None,
        normalized_value: Any | None,
        stage: str | None,
        field_name: str | None,
    ) -> None:
        key = (code.value, field_path, message)
        if key in self._seen:
            return
        self._seen.add(key)
        derived_stage, derived_field_name = _derive_issue_location(field_path)
        bucket.append(
            LegadoImportIssue(
                code=code,
                error_code=code,
                message=message,
                field=field_path,
                severity=severity,
                source_path=field_path,
                stage=stage or derived_stage,
                field_name=field_name or derived_field_name,
                raw_value=raw_value,
                normalized_value=normalized_value,
            )
        )


def validate_legado_source(source: dict[str, Any]) -> LegadoValidationReport:
    report = LegadoValidationReport()
    if not isinstance(source, dict):
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            "Legado source must be a JSON object",
            "source",
            raw_value=source,
        )
        return report

    for field_name, value in source.items():
        _validate_top_level_field(report, field_name, value)

    _ensure_required_top_level_fields(report, source)
    _validate_nested_stage_fields(report, source)
    return report


def validate_mapped_online_source(
    report: LegadoValidationReport,
    *,
    normalized_base_url: str,
    normalized_definition: dict[str, Any],
) -> None:
    try:
        validate_phase1_source_definition(normalized_base_url, normalized_definition)
    except OnlineSourceValidationError as exc:
        _translate_phase1_validation_error(report, str(exc))


def _validate_top_level_field(report: LegadoValidationReport, field_name: str, value: Any) -> None:
    normalized_name = field_name.strip()
    lowered_name = normalized_name.lower()

    if normalized_name in SUPPORTED_TOP_LEVEL_FIELDS:
        if normalized_name == "header":
            _validate_header_mapping(report, value, normalized_name)
            return
        _validate_value(report, value, normalized_name)
        return

    if normalized_name in IGNORED_TOP_LEVEL_FIELDS:
        report.add_warning(
            LegadoImportCode.IGNORED_FIELD,
            f"{normalized_name} is ignored during strict whitelist import",
            normalized_name,
            raw_value=value,
        )
        return

    code = FORBIDDEN_FIELD_CODES.get(lowered_name)
    if code is not None:
        report.add_error(
            code,
            f"{normalized_name} is not supported in Phase 2 whitelist import",
            normalized_name,
            raw_value=value,
        )
        return

    report.add_error(
        LegadoImportCode.UNSUPPORTED_FIELD,
        f"{normalized_name} is outside the Phase 2 whitelist",
        normalized_name,
        raw_value=value,
    )
    _validate_value(report, value, normalized_name)


def _validate_nested_stage_fields(report: LegadoValidationReport, source: dict[str, Any]) -> None:
    for stage_name, supported_fields in STAGE_SUPPORTED_FIELDS.items():
        if stage_name not in source:
            continue
        stage_value = source[stage_name]
        if not isinstance(stage_value, dict):
            report.add_error(
                LegadoImportCode.MAPPING_FAILED,
                f"{stage_name} must be an object",
                stage_name,
                raw_value=stage_value,
            )
            continue
        ignored_fields = STAGE_IGNORED_FIELDS[stage_name]
        for field_name, field_value in stage_value.items():
            field_path = f"{stage_name}.{field_name}"
            lowered_name = field_name.lower()
            if field_name in supported_fields:
                _validate_value(report, field_value, field_path)
                continue
            if field_name in ignored_fields:
                report.add_warning(
                    LegadoImportCode.IGNORED_FIELD,
                    f"{field_path} is ignored during strict whitelist import",
                    field_path,
                    raw_value=field_value,
                )
                continue
            code = FORBIDDEN_FIELD_CODES.get(lowered_name, LegadoImportCode.UNSUPPORTED_FIELD)
            report.add_error(
                code,
                f"{field_path} is not supported in Phase 2 whitelist import",
                field_path,
                raw_value=field_value,
            )
            _validate_value(report, field_value, field_path)


def _ensure_required_top_level_fields(report: LegadoValidationReport, source: dict[str, Any]) -> None:
    required_fields = {
        "bookSourceName",
        "bookSourceUrl",
        "searchUrl",
        "ruleSearch",
        "ruleBookInfo",
        "ruleToc",
        "ruleContent",
    }
    for field_name in required_fields:
        if field_name not in source:
            report.add_error(
                LegadoImportCode.REQUIRED_FIELD_MISSING,
                f"{field_name} is required for strict whitelist import",
                field_name,
                raw_value=None,
            )


def _validate_value(report: LegadoValidationReport, value: Any, field_path: str) -> None:
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            normalized_nested_key = str(nested_key).strip().lower()
            if normalized_nested_key in FORBIDDEN_FIELD_CODES:
                report.add_error(
                    FORBIDDEN_FIELD_CODES[normalized_nested_key],
                    f"{field_path}.{nested_key} is not supported in Phase 2 whitelist import",
                    f"{field_path}.{nested_key}",
                    raw_value=nested_value,
                )
            _validate_value(report, nested_value, f"{field_path}.{nested_key}")
        return

    if isinstance(value, list):
        report.add_error(
            LegadoImportCode.UNSUPPORTED_MULTI_REQUEST,
            f"{field_path} uses a list, which is outside the whitelist importer",
            field_path,
            raw_value=value,
        )
        return

    if isinstance(value, str):
        _validate_string(report, value, field_path)


def _validate_header_mapping(report: LegadoValidationReport, value: Any, field_path: str) -> None:
    if not isinstance(value, dict):
        report.add_error(
            LegadoImportCode.MAPPING_FAILED,
            f"{field_path} must be an object of static header key/value pairs",
            field_path,
            raw_value=value,
        )
        return

    for header_name, header_value in value.items():
        lowered_name = str(header_name).strip().lower()
        header_path = f"{field_path}.{header_name}"
        if lowered_name == "cookie":
            report.add_error(
                LegadoImportCode.UNSUPPORTED_COOKIE,
                "Cookie headers are not supported",
                header_path,
                raw_value=header_value,
            )
        if lowered_name == "authorization":
            report.add_error(
                LegadoImportCode.UNSUPPORTED_AUTHORIZATION,
                "Authorization headers are not supported",
                header_path,
                raw_value=header_value,
            )
        _validate_value(report, header_value, header_path)


def _validate_string(report: LegadoValidationReport, value: str, field_path: str) -> None:
    lowered_value = value.strip().lower()
    for pattern, code in FORBIDDEN_STRING_PATTERNS.items():
        if pattern in lowered_value:
            report.add_error(
                code,
                f"{field_path} contains unsupported pattern: {pattern}",
                field_path,
                raw_value=value,
            )

    for placeholder in PLACEHOLDER_PATTERN.findall(value):
        if placeholder not in ALLOWED_RAW_PLACEHOLDERS:
            report.add_error(
                LegadoImportCode.UNSUPPORTED_PLACEHOLDER,
                f"{field_path} uses unsupported placeholder: {placeholder}",
                field_path,
                raw_value=value,
            )


def _translate_phase1_validation_error(report: LegadoValidationReport, message: str) -> None:
    lowered_message = message.lower()
    if "placeholder" in lowered_message:
        report.add_error(LegadoImportCode.UNSUPPORTED_PLACEHOLDER, message)
        return
    if "http/https" in lowered_message or "runtime url" in lowered_message or "url" in lowered_message:
        report.add_error(LegadoImportCode.INVALID_URL, message)
        return
    if "missing required field" in lowered_message or "requires list_selector" in lowered_message:
        report.add_error(LegadoImportCode.REQUIRED_FIELD_MISSING, message)
        return
    if "authorization" in lowered_message:
        report.add_error(LegadoImportCode.UNSUPPORTED_AUTHORIZATION, message)
        return
    if "cookie" in lowered_message:
        report.add_error(LegadoImportCode.UNSUPPORTED_COOKIE, message)
        return
    if "unsupported parser" in lowered_message:
        report.add_error(LegadoImportCode.UNSUPPORTED_PARSER, message)
        return
    if "unsupported capability" in lowered_message:
        report.add_error(LegadoImportCode.MAPPING_FAILED, message)
        return
    report.add_error(LegadoImportCode.MAPPING_FAILED, message)


def _derive_issue_location(field_path: str | None) -> tuple[str | None, str | None]:
    if not field_path:
        return None, None
    if field_path == "source":
        return "source", None
    if field_path == "ruleSearch":
        return "search", "ruleSearch"
    if field_path == "ruleBookInfo":
        return "detail", "ruleBookInfo"
    if field_path == "ruleToc":
        return "catalog", "ruleToc"
    if field_path == "ruleContent":
        return "content", "ruleContent"
    if field_path.startswith("ruleSearch."):
        return "search", field_path.split(".")[-1]
    if field_path.startswith("ruleBookInfo."):
        return "detail", field_path.split(".")[-1]
    if field_path.startswith("ruleToc."):
        return "catalog", field_path.split(".")[-1]
    if field_path.startswith("ruleContent."):
        return "content", field_path.split(".")[-1]
    if "." not in field_path:
        return "source", field_path
    return "source", field_path.split(".")[-1]
