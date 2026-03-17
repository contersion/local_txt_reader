# Legado Import Traceability 索引（Phase 2）

本文档用于把当前 Phase 2 静态 importer 的相关文档、样本、测试和错误码串起来。

- 字段/能力 -> 支持状态 -> canonical 映射
- 字段/能力 -> 样本 ID
- 样本 ID -> 回归测试函数
- 字段/能力 -> 错误码或 warning 码
- 文档 -> 代码 -> 测试

目标是：当有人问“这个字段是否支持”或“哪条测试证明了这个行为”时，这份索引能直接回答，不再依赖占位项。

---

## 1. 相关文档

当前 importer 行为由以下文档共同约束：

- [Legado Phase 2 文档总览](./LEGADO_PHASE2_INDEX.md)
  - 阶段定位
  - 阅读顺序
  - 文档导航
- [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
  - 字段白名单
  - canonical 映射目标
  - reject 与 ignore 边界
- [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
  - 稳定的 importer error / warning 码
  - fatal 与 non-fatal 语义
- [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
  - 最小稳定样本集
  - 样本分类与覆盖目标
- [Legado Import Issue Schema（Phase 2）](./LEGADO_IMPORT_ISSUE_SCHEMA.md)
  - importer issue 结构契约
  - 定位与归一化元信息
- [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
  - 字段、样本、测试与错误码的交叉索引

---

## 1.1 实现入口

当前 Phase 2 importer 的主要实现入口为：

- `backend/app/services/online/legado_validator.py`
- `backend/app/services/online/legado_mapper.py`
- `backend/app/services/online/legado_importer.py`
- `backend/app/routers/online_source_import.py`
- `backend/tests/test_legado_import_api.py`

因此本文档中的追踪链默认是：

- 文档 -> 样本 -> 测试 -> 实现入口

---

## 2. 冻结范围

Phase 2 当前仍表示：

- 严格白名单 importer
- 仅允许静态 alias 映射
- 仅允许静态 CSS / JSoup 归一化
- 仅做静态校验与文档化
- 继续复用现有 discovery 执行链

Phase 2 当前**仍不包含**：

- JS 执行
- Cookie / 登录态
- WebView
- proxy 运行时
- 多请求链式执行
- 复杂变量系统
- 条件 DSL
- replace / clean DSL 运行时
- 高兼容执行环境

---

## 3. 样本 ID 索引

| 样本 ID | 类别 | 样本名称 | 主要测试 |
| --- | --- | --- | --- |
| `S1` | success | `VALID_LEGADO_SOURCE` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_import_legado_source_persists_online_source`, `test_imported_legado_source_can_run_existing_discovery_search`, `test_imported_legado_source_can_run_detail_catalog_and_chapter_chain` |
| `S2` | success | `VALID_LEGADO_ALIAS_SOURCE` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_imported_alias_source_can_run_existing_discovery_search` |
| `S3` | warning | display-only metadata sample | `test_validate_legado_import_warns_and_ignores_display_fields` |
| `S4` | reject | JS content rule sample | `test_validate_legado_import_rejects_js` |
| `S5` | reject | Cookie / login-state sample | `test_validate_legado_import_rejects_cookie_and_login_state` |
| `S6` | reject | webView / proxy sample | `test_validate_legado_import_rejects_webview_and_proxy` |
| `S7` | reject | charset override sample | `test_validate_legado_import_rejects_charset_override` |
| `S8` | reject | replace DSL sample | `test_validate_legado_import_rejects_replace_dsl` |
| `S9` | reject | unknown display-like field sample | `test_validate_legado_import_unknown_display_like_field_is_hard_error`, `test_validate_legado_import_unknown_field_returns_precise_location` |
| `S10` | reject | unsupported placeholder sample | `test_validate_legado_import_rejects_unknown_placeholder` |
| `S11` | warning | `selector@html` normalization sample | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` |
| `S12` | warning | source-level ignored metadata sample | `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields` |
| `S13` | success | absolute search URL sample | `test_validate_legado_import_accepts_absolute_search_url` |
| `S14` | reject | unsupported parser prefix sample | `test_validate_legado_import_rejects_unsupported_parser_prefix` |
| `S15` | reject | complex HTML DSL sample | `test_validate_legado_import_rejects_complex_html_dsl` |
| `S16` | warning | search-stage ignored metadata sample | `test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields` |
| `S17` | warning | detail-stage ignored metadata sample | `test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields` |
| `S18` | success | detail URL bridge sample | `test_validate_legado_import_exposes_detail_url_bridge_placeholder` |
| `S19` | success | catalog URL bridge sample | `test_validate_legado_import_exposes_catalog_url_bridge_placeholder` |
| `S20` | success | chapter URL bridge sample | `test_validate_legado_import_exposes_chapter_url_bridge_placeholder` |
| `S21` | reject | Authorization header sample | `test_validate_legado_import_rejects_authorization_header` |
| `S22` | reject | dynamic variable sample | `test_validate_legado_import_rejects_dynamic_variable_fields` |
| `S23` | reject | condition DSL sample | `test_validate_legado_import_rejects_condition_dsl` |
| `S24` | reject | unsupported method sample | `test_validate_legado_import_rejects_unsupported_method` |
| `S25` | reject | multi request sample | `test_validate_legado_import_rejects_multi_request_structures` |
| `S26` | reject | dynamic request sample | `test_validate_legado_import_rejects_dynamic_request_patterns` |
| `S27` | reject | invalid base URL sample | `test_validate_legado_import_rejects_invalid_base_url` |
| `S28` | reject | missing required top-level field sample | `test_validate_legado_import_rejects_missing_required_stage_definition` |
| `S29` | reject | invalid stage shape sample | `test_validate_legado_import_rejects_invalid_stage_shape` |

---

## 4. Source 层字段

| Legado 字段 | 支持状态 | canonical 目标 | 样本 ID | 回归测试 | 错误码 / 备注 |
| --- | --- | --- | --- | --- | --- |
| `bookSourceName` | supported | `name` | `S1`, `S2` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | - |
| `bookSourceComment` | supported | `description` | `S1`, `S2` | same as above | normalized as plain text |
| `bookSourceUrl` | supported | `base_url` | `S1`, `S2`, `S13` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_accepts_absolute_search_url` | absolute URL acceptance is explicitly covered by `S13` |
| `enabled` | supported | `enabled` | `S1`, `S2` | same as above | - |
| `bookSourceGroup` | warning + ignore | - | `S3` | `test_validate_legado_import_warns_and_ignores_display_fields` | `LEGADO_IGNORED_FIELD` |
| `bookSourceType` | warning + ignore | - | `S12` | `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields` | `LEGADO_IGNORED_FIELD` |
| `customOrder` | warning + ignore | - | `S3` | `test_validate_legado_import_warns_and_ignores_display_fields` | `LEGADO_IGNORED_FIELD` |
| `weight` | warning + ignore | - | `S3` | `test_validate_legado_import_warns_and_ignores_display_fields` | `LEGADO_IGNORED_FIELD` |
| `lastUpdateTime` | warning + ignore | - | `S12` | `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields` | `LEGADO_IGNORED_FIELD` |
| `respondTime` | warning + ignore | - | `S12` | `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields` | `LEGADO_IGNORED_FIELD` |
| unknown source-level field | reject | - | `S9` | `test_validate_legado_import_unknown_display_like_field_is_hard_error`, `test_validate_legado_import_unknown_field_returns_precise_location` | `LEGADO_UNSUPPORTED_FIELD` |

---

## 5. 请求层

| 能力 | 支持状态 | canonical 目标 | 样本 ID | 回归测试 | 错误码 / 备注 |
| --- | --- | --- | --- | --- | --- |
| `searchUrl` static single request | supported | `definition.search.request` | `S1`, `S2`, `S13` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_accepts_absolute_search_url` | - |
| `GET` | supported | `request.method` | `S1`, `S13` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_accepts_absolute_search_url` | - |
| `POST` | supported | `request.method` | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_imported_alias_source_can_run_existing_discovery_search` | lower-case input normalized to `POST` |
| static `header` | supported | `request.headers` | `S1`, `S2` | same as above | cookie/auth excluded |
| static `body` | supported | `request.body` | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | string body normalized into mapping |
| relative URL | supported | `request.url` | `S1`, `S2` | same as above | normalized against `base_url` in runtime |
| absolute URL | supported | `request.url` | `S13` | `test_validate_legado_import_accepts_absolute_search_url` | explicitly covered |
| `Authorization` header | reject | - | `S21` | `test_validate_legado_import_rejects_authorization_header` | `LEGADO_UNSUPPORTED_AUTHORIZATION` |
| unsupported HTTP method | reject | - | `S24` | `test_validate_legado_import_rejects_unsupported_method` | `LEGADO_UNSUPPORTED_METHOD` |
| dynamic request expression | reject | - | `S26` | `test_validate_legado_import_rejects_dynamic_request_patterns` | `LEGADO_UNSUPPORTED_DYNAMIC_REQUEST` |
| `charset` override | reject | - | `S7` | `test_validate_legado_import_rejects_charset_override` | `LEGADO_UNSUPPORTED_CHARSET_OVERRIDE` |
| `proxy` | reject | - | `S6` | `test_validate_legado_import_rejects_webview_and_proxy` | `LEGADO_UNSUPPORTED_PROXY` |
| `webView` | reject | - | `S6` | `test_validate_legado_import_rejects_webview_and_proxy` | `LEGADO_UNSUPPORTED_WEBVIEW` |
| invalid base URL | reject | - | `S27` | `test_validate_legado_import_rejects_invalid_base_url` | `LEGADO_INVALID_URL` |

---

## 6. 占位符

| 占位符 | 支持状态 | 归一化结果 | 样本 ID | 回归测试 | 错误码 / 备注 |
| --- | --- | --- | --- | --- | --- |
| `{{key}}` | supported | `{{keyword}}` | `S1`, `S2`, `S13` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_accepts_absolute_search_url` | alias normalization |
| `{{page}}` | supported | `{{page}}` | `S1`, `S2`, `S13` | same as above | preserved |
| `{{detail_url}}` | supported | `{{detail_url}}` | `S18` | `test_validate_legado_import_exposes_detail_url_bridge_placeholder` | generated canonical placeholder |
| `{{catalog_url}}` | supported | `{{catalog_url}}` | `S19` | `test_validate_legado_import_exposes_catalog_url_bridge_placeholder` | generated canonical placeholder |
| `{{chapter_url}}` | supported | `{{chapter_url}}` | `S20` | `test_validate_legado_import_exposes_chapter_url_bridge_placeholder` | generated canonical placeholder |
| unsupported placeholder | reject | - | `S10` | `test_validate_legado_import_rejects_unknown_placeholder` | `LEGADO_UNSUPPORTED_PLACEHOLDER` |

---

## 7. Parser 家族

| Parser 写法 | 支持状态 | 归一化结果 | 样本 ID | 回归测试 | 错误码 / 备注 |
| --- | --- | --- | --- | --- | --- |
| `css:` | supported | `css` | `S1` | `test_validate_legado_import_accepts_supported_whitelist_source` | - |
| `jsoup:` | supported | `css` | `S2`, `S11` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | static alias only |
| `jsonpath:` | supported | `jsonpath` | `S1` | `test_validate_legado_import_accepts_supported_whitelist_source` | - |
| `json:` | supported | `jsonpath` | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | static alias only |
| `xpath:` | supported | `xpath` | `S1`, `S2` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | - |
| `regex:` | supported | `regex` | `S1` | `test_validate_legado_import_accepts_supported_whitelist_source` | regex group kept when present |
| unsupported parser | reject | - | `S14` | `test_validate_legado_import_rejects_unsupported_parser_prefix` | `LEGADO_UNSUPPORTED_PARSER` |

---

## 8. CSS / JSoup 语法归一化

| 语法 | 支持状态 | 归一化结果 | 样本 ID | 回归测试 | 错误码 / 备注 |
| --- | --- | --- | --- | --- | --- |
| `selector@text` | supported | `parser=css, expr=selector` | `S1`, `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | `attr=text` intentionally omitted |
| `selector@href` | supported | `attr=href` | `S1`, `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | - |
| `selector@src` | supported | `attr=src` | `S1`, `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | - |
| `selector@html` | warning | summarized as `{"parser":"css","expr":"..."}` | `S11` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | `LEGADO_CSS_HTML_NORMALIZED` |
| complex HTML DSL | reject | - | `S15` | `test_validate_legado_import_rejects_complex_html_dsl` | `LEGADO_UNSUPPORTED_PARSER` |

---

## 9. 分阶段字段映射

### Search 阶段

| 字段 | alias | 支持状态 | canonical 目标 | 样本 ID | 回归测试 |
| --- | --- | --- | --- | --- | --- |
| `bookList` | `list` | supported | `definition.search.list_selector` | `S1`, `S2` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` |
| `name` | `bookName` | supported | `definition.search.fields.title` | `S1`, `S2` | same as above |
| `bookUrl` | `url` | supported | `definition.search.fields.detail_url` | `S1`, `S2` | same as above |
| `author` | - | supported | `definition.search.fields.author` | `S1`, `S2` | same as above |
| `intro` | `desc`, `description` | supported | `definition.search.fields.description` | `S1`, `S2` | same as above |
| `coverUrl` | `cover` | supported | `definition.search.fields.cover_url` | `S1`, `S2` | same as above |
| `bookId` | `id` | supported | `definition.search.fields.remote_book_id` | `S1`, `S2` | same as above |
| `kind`, `lastChapter`, `wordCount`, `updateTime` | - | warning + ignore | - | `S16` | `test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields` |

### Detail 阶段

| 字段 | alias | 支持状态 | canonical 目标 | 样本 ID | 回归测试 |
| --- | --- | --- | --- | --- | --- |
| `name` | `bookName` | supported | `definition.detail.fields.title` | `S1`, `S2` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` |
| `author` | - | supported | `definition.detail.fields.author` | `S1`, `S2` | same as above |
| `intro` | `desc`, `description` | supported | `definition.detail.fields.description` | `S1`, `S2` | same as above |
| `coverUrl` | `cover` | supported | `definition.detail.fields.cover_url` | `S1`, `S2` | same as above |
| `tocUrl` | `catalogUrl`, `chapterUrl` | supported | `definition.detail.fields.catalog_url` | `S1`, `S2` | same as above |
| `kind`, `lastChapter`, `wordCount`, `updateTime` | - | warning + ignore | - | `S17` | `test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields` |

### Catalog 阶段

| 字段 | alias | 支持状态 | canonical 目标 | 样本 ID | 回归测试 |
| --- | --- | --- | --- | --- | --- |
| `chapterList` | `list` | supported | `definition.catalog.list_selector` | `S1`, `S2` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` |
| `chapterName` | `name` | supported | `definition.catalog.fields.chapter_title` | `S1`, `S2` | same as above |
| `chapterUrl` | `url` | supported | `definition.catalog.fields.chapter_url` | `S1`, `S2` | same as above |

### Content 阶段

| 字段 | alias | 支持状态 | canonical 目标 | 样本 ID | 回归测试 |
| --- | --- | --- | --- | --- | --- |
| `content` | `text`, `body` | supported | `definition.content.fields.content` | `S1`, `S2`, `S11`, `S15` | `test_validate_legado_import_accepts_supported_whitelist_source`, `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_rejects_complex_html_dsl` |

---

## 10. Reject / Warning 能力索引

| 能力 | 错误码 | 样本 ID | 回归测试 | 备注 |
| --- | --- | --- | --- | --- |
| JS execution | `LEGADO_UNSUPPORTED_JS` | `S4` | `test_validate_legado_import_rejects_js` | precise location metadata also asserted |
| Cookie | `LEGADO_UNSUPPORTED_COOKIE` | `S5` | `test_validate_legado_import_rejects_cookie_and_login_state` | precise location metadata also asserted |
| Authorization header | `LEGADO_UNSUPPORTED_AUTHORIZATION` | `S21` | `test_validate_legado_import_rejects_authorization_header` | single-issue dedupe is asserted |
| login state | `LEGADO_UNSUPPORTED_LOGIN_STATE` | `S5` | `test_validate_legado_import_rejects_cookie_and_login_state` | currently covered via `loginUrl` |
| WebView | `LEGADO_UNSUPPORTED_WEBVIEW` | `S6` | `test_validate_legado_import_rejects_webview_and_proxy` | precise location metadata also asserted |
| proxy | `LEGADO_UNSUPPORTED_PROXY` | `S6` | `test_validate_legado_import_rejects_webview_and_proxy` | - |
| dynamic variable | `LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE` | `S22` | `test_validate_legado_import_rejects_dynamic_variable_fields` | source-level whitelist rejection |
| condition DSL | `LEGADO_UNSUPPORTED_CONDITION_DSL` | `S23` | `test_validate_legado_import_rejects_condition_dsl` | source-level whitelist rejection |
| unsupported method | `LEGADO_UNSUPPORTED_METHOD` | `S24` | `test_validate_legado_import_rejects_unsupported_method` | request whitelist enforcement |
| charset override | `LEGADO_UNSUPPORTED_CHARSET_OVERRIDE` | `S7` | `test_validate_legado_import_rejects_charset_override` | precise location metadata also asserted |
| replace DSL | `LEGADO_UNSUPPORTED_REPLACE_DSL` | `S8` | `test_validate_legado_import_rejects_replace_dsl` | - |
| multi request | `LEGADO_UNSUPPORTED_MULTI_REQUEST` | `S25` | `test_validate_legado_import_rejects_multi_request_structures` | single-issue dedupe is asserted |
| dynamic request | `LEGADO_UNSUPPORTED_DYNAMIC_REQUEST` | `S26` | `test_validate_legado_import_rejects_dynamic_request_patterns` | string-pattern rejection |
| unknown field | `LEGADO_UNSUPPORTED_FIELD` | `S9` | `test_validate_legado_import_unknown_display_like_field_is_hard_error`, `test_validate_legado_import_unknown_field_returns_precise_location` | strict unknown-field rejection |
| invalid URL | `LEGADO_INVALID_URL` | `S27` | `test_validate_legado_import_rejects_invalid_base_url` | mapped canonical validation failure |
| required field missing | `LEGADO_REQUIRED_FIELD_MISSING` | `S28` | `test_validate_legado_import_rejects_missing_required_stage_definition` | top-level stage requirement enforced |
| mapping failed | `LEGADO_MAPPING_FAILED` | `S29` | `test_validate_legado_import_rejects_invalid_stage_shape` | invalid object shape rejection |
| unsupported placeholder | `LEGADO_UNSUPPORTED_PLACEHOLDER` | `S10` | `test_validate_legado_import_rejects_unknown_placeholder` | - |
| ignored display field | `LEGADO_IGNORED_FIELD` | `S3`, `S12`, `S16`, `S17` | `test_validate_legado_import_warns_and_ignores_display_fields`, `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields`, `test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields`, `test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields` | warning path |
| `selector@html` normalization | `LEGADO_CSS_HTML_NORMALIZED` | `S11` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | warning path with raw/normalized comparison |
| unsupported parser prefix | `LEGADO_UNSUPPORTED_PARSER` | `S14` | `test_validate_legado_import_rejects_unsupported_parser_prefix` | parser-like prefix hard rejection |
| complex HTML DSL | `LEGADO_UNSUPPORTED_PARSER` | `S15` | `test_validate_legado_import_rejects_complex_html_dsl` | nested parser syntax hard rejection |

---

## 11. 归一化行为索引

| 归一化行为 | 样本 ID | 回归测试 | 结果 |
| --- | --- | --- | --- |
| `{{key}} -> {{keyword}}` | `S1`, `S2`, `S13` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_accepts_absolute_search_url` | canonical placeholder normalization |
| lowercase `post` -> `POST` | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | canonical method normalization |
| string body -> key/value body mapping | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | canonical body normalization |
| `jsoup:` -> `css` | `S2`, `S11`, `S15` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`, `test_validate_legado_import_rejects_complex_html_dsl` | canonical parser alias normalization |
| `json:` -> `jsonpath` | `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | canonical parser alias normalization |
| `selector@text` -> plain CSS text extraction | `S1`, `S2` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | `attr=text` intentionally omitted |
| `selector@html` -> summarized CSS warning normalization | `S11` | `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms` | warning includes raw/normalized summary |
| absolute search URL preserved | `S13` | `test_validate_legado_import_accepts_absolute_search_url` | canonical request URL remains absolute |
| search detail link -> `{{detail_url}}` bridge | `S18` | `test_validate_legado_import_exposes_detail_url_bridge_placeholder` | detail stage request placeholder bridge |
| detail catalog link -> `{{catalog_url}}` bridge | `S19` | `test_validate_legado_import_exposes_catalog_url_bridge_placeholder` | catalog stage request placeholder bridge |
| catalog chapter link -> `{{chapter_url}}` bridge | `S20` | `test_validate_legado_import_exposes_chapter_url_bridge_placeholder` | content stage request placeholder bridge |

---

## 12. 维护约定

1. If a new sample is added, update:
   - [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
   - this traceability index
   - `test_legado_import_api.py`
2. If a new error or warning code is added, update:
   - [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
   - this traceability index
   - affected sample entries
3. If a field gains support, update:
   - [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
   - this traceability index
   - the covering sample/test
4. Do not silently upgrade Phase 2 into runtime compatibility.
