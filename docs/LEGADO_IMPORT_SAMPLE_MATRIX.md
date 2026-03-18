# Legado Import 样本矩阵（Phase 2）

本文档定义当前 Phase 2 静态 importer 的最小样本集，用于固定 importer 行为并支撑回归测试。

## 适用范围

- 仅针对 importer
- 仅针对静态映射
- 不引入新的运行时能力
- 导入成功后的书源继续复用现有 discovery 执行链

所有文档化样本都应能在 [test_legado_import_api.py](../backend/tests/test_legado_import_api.py) 中找到对应回归测试。

## 相关文档

- [Legado Phase 2 文档总览](./LEGADO_PHASE2_INDEX.md)
- [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
- [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
- [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
- [Legado Import Issue Schema（Phase 2）](./LEGADO_IMPORT_ISSUE_SCHEMA.md)

---

## 样本覆盖摘要

- 当前样本总数：`29`
- 分类概览：`success = 6`、`warning = 5`、`reject = 18`
- Phase 2 验收基线样本范围：`S1-S29`
- 当前矩阵用于固定 Legado 静态 importer 第一阶段的最小样本闭环；新增样本时不得改写现有样本编号语义。

---

## 样本类别

- `success`
  - 样本应通过 validate，并在适用时导入成功
- `warning`
  - 样本应通过 validate / import，但返回 warnings
- `reject`
  - 样本应以显式 `hard error` 失败

---

## S1. 最小合法白名单样本

- 样本类别：`success`
- 样本名称：`VALID_LEGADO_SOURCE`
- 对应测试：
  - `test_validate_legado_import_accepts_supported_whitelist_source`
  - `test_import_legado_source_persists_online_source`
  - `test_imported_legado_source_can_run_existing_discovery_search`
  - `test_imported_legado_source_can_run_detail_catalog_and_chapter_chain`
- 样本目的：
  - Prove the minimum Phase 2 whitelist path works end-to-end.
- 关键字段：
  - `bookSourceName`
  - `bookSourceUrl`
  - `searchUrl`
  - `ruleSearch.bookList/name/bookUrl`
  - `ruleBookInfo.name/tocUrl`
  - `ruleToc.chapterList/chapterName/chapterUrl`
  - `ruleContent.content`
- 预期结果：
  - `is_valid = true`
  - import succeeds
  - imported source can run existing discovery search
  - imported source can run detail/catalog/chapter discovery chain
- 覆盖能力：
  - static `searchUrl`
  - canonical field mapping
  - `css/jsonpath/xpath/regex`
  - `{{key}} -> {{keyword}}`
  - `{{page}}`

---

## S2. Alias 密集合法样本

- 样本类别：`success`
- 样本名称：`VALID_LEGADO_ALIAS_SOURCE`
- 对应测试：
  - `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`
  - `test_imported_alias_source_can_run_existing_discovery_search`
- 样本目的：
  - Prove high-frequency static aliases still normalize into the same canonical structure.
- 关键字段：
  - `ruleSearch.list/bookName/url/desc/cover/id`
  - `ruleBookInfo.bookName/description/cover/catalogUrl`
  - `ruleToc.list/name/url`
  - `ruleContent.text`
  - `searchUrl` with lowercase `post`, `header`, string `body`
- 预期结果：
  - `is_valid = true`
  - import succeeds
  - imported source still works with existing discovery search
- 覆盖能力：
  - alias normalization
  - `jsoup:` -> `css`
  - `json:` -> `jsonpath`
  - `selector@text`
  - `selector@href`
  - `selector@src`
  - static body normalization
  - `POST`

---

## S3. Warning + Ignore 展示字段样本

- 样本类别：`warning`
- 样本名称：display-only metadata sample
- 对应测试：
  - `test_validate_legado_import_warns_and_ignores_display_fields`
- 样本目的：
  - Prove explicitly whitelisted display/meta fields degrade to warning instead of failure.
- 关键字段：
  - `bookSourceGroup`
  - `customOrder`
  - `weight`
- 预期结果：
  - `is_valid = true`
  - warnings include `LEGADO_IGNORED_FIELD`
  - `ignored_fields` lists the dropped keys
- 覆盖能力：
  - warning + ignore whitelist

---

## S4. JS 拒绝样本

- 样本类别：`reject`
- 样本名称：JS content rule sample
- 对应测试：
  - `test_validate_legado_import_rejects_js`
- 样本目的：
  - Prove any JS-driven content rule is blocked before import.
- 关键字段：
  - `ruleContent.content = "@js:..."`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_JS`
- 覆盖能力：
  - JS rejection

---

## S5. Cookie / 登录态拒绝样本

- 样本类别：`reject`
- 样本名称：authenticated-source sample
- 对应测试：
  - `test_validate_legado_import_rejects_cookie_and_login_state`
- 样本目的：
  - Prove session/cookie/login semantics are rejected at importer time.
- 关键字段：
  - `header.Cookie`
  - `loginUrl`
- 预期结果：
  - `is_valid = false`
  - fatal error codes:
    - `LEGADO_UNSUPPORTED_COOKIE`
    - `LEGADO_UNSUPPORTED_LOGIN_STATE`
- 覆盖能力：
  - cookie rejection
  - login-state rejection

---

## S6. webView / Proxy 拒绝样本

- 样本类别：`reject`
- 样本名称：browser/proxy sample
- 对应测试：
  - `test_validate_legado_import_rejects_webview_and_proxy`
- 样本目的：
  - Prove browser/proxy runtime concepts do not enter Phase 2.
- 关键字段：
  - `webView`
  - `proxy`
- 预期结果：
  - `is_valid = false`
  - fatal error codes:
    - `LEGADO_UNSUPPORTED_WEBVIEW`
    - `LEGADO_UNSUPPORTED_PROXY`
- 覆盖能力：
  - webView rejection
  - proxy rejection

---

## S7. Charset Override 拒绝样本

- 样本类别：`reject`
- 样本名称：charset override sample
- 对应测试：
  - `test_validate_legado_import_rejects_charset_override`
- 样本目的：
  - Prove explicit charset override is still outside the importer contract.
- 关键字段：
  - `charset`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_CHARSET_OVERRIDE`
- 覆盖能力：
  - charset override rejection

---

## S8. Replace DSL 拒绝样本

- 样本类别：`reject`
- 样本名称：replace-rule sample
- 对应测试：
  - `test_validate_legado_import_rejects_replace_dsl`
- 样本目的：
  - Prove configurable replace/clean DSL is not silently accepted.
- 关键字段：
  - `replaceRule`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_REPLACE_DSL`
- 覆盖能力：
  - replace DSL rejection

---

## S9. 未知字段拒绝样本

- 样本类别：`reject`
- 样本名称：display-like unknown field sample
- 对应测试：
  - `test_validate_legado_import_unknown_display_like_field_is_hard_error`
- 样本目的：
  - Prove unknown fields are not auto-downgraded into warning + ignore.
- 关键字段：
  - `themeColor`
- 预期结果：
  - `is_valid = false`
  - no warnings
  - fatal error code `LEGADO_UNSUPPORTED_FIELD`
- 覆盖能力：
  - strict unknown-field rejection
  - frozen ignore boundary

---

## S10. 未知占位符拒绝样本

- 样本类别：`reject`
- 样本名称：unsupported placeholder sample
- 对应测试：
  - `test_validate_legado_import_rejects_unknown_placeholder`
- 样本目的：
  - Prove whitelist placeholders remain strict.
- 关键字段：
  - `searchUrl` with `{{secret}}`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_PLACEHOLDER`
- 覆盖能力：
  - placeholder whitelist enforcement

---

## S11. CSS / JSoup 静态归一化样本

- 样本类别：`warning`
- 样本名称：`selector@html` normalization sample
- 对应测试：
  - `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`
- 样本目的：
  - Prove `selector@html` is accepted only via a controlled importer normalization path.
- 关键字段：
  - `ruleContent.text = "jsoup:#content@html"`
- 预期结果：
  - `is_valid = true`
  - warning code `LEGADO_CSS_HTML_NORMALIZED`
  - canonical content rule becomes CSS-based static extraction
- 覆盖能力：
  - `jsoup:` normalization
  - controlled `@html` compatibility

---

## S12. Source 层忽略元信息样本

- 样本类别：`warning`
- 样本名称：source-level ignored metadata sample
- 对应测试：
  - `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields`
- 样本目的：
  - Prove explicitly ignored source-level metadata fields still produce warning + ignore rather than failure.
- 关键字段：
  - `bookSourceType`
  - `lastUpdateTime`
  - `respondTime`
- 预期结果：
  - `is_valid = true`
  - warnings include `LEGADO_IGNORED_FIELD`
  - `ignored_fields` contains all three keys
- 覆盖能力：
  - source-level ignored metadata whitelist

---

## S13. 绝对 URL 成功样本

- 样本类别：`success`
- 样本名称：absolute search URL sample
- 对应测试：
  - `test_validate_legado_import_accepts_absolute_search_url`
- 样本目的：
  - Prove absolute HTTP search URLs are still valid importer input.
- 关键字段：
  - `searchUrl` using an absolute `https://` URL
- 预期结果：
  - `is_valid = true`
  - canonical search request URL remains absolute
- 覆盖能力：
  - absolute URL acceptance

---

## S14. Unsupported Parser Prefix 拒绝样本

- 样本类别：`reject`
- 样本名称：unsupported parser prefix sample
- 对应测试：
  - `test_validate_legado_import_rejects_unsupported_parser_prefix`
- 样本目的：
  - Prove parser-like prefixes outside the whitelist are rejected instead of silently treated as CSS.
- 关键字段：
  - `ruleSearch.bookList = "jq:.result-item"`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_PARSER`
- 覆盖能力：
  - unsupported parser rejection

---

## S15. 复杂 HTML DSL 拒绝样本

- 样本类别：`reject`
- 样本名称：complex HTML DSL sample
- 对应测试：
  - `test_validate_legado_import_rejects_complex_html_dsl`
- 样本目的：
  - Prove nested parser-style HTML DSL is rejected instead of being treated as plain attr extraction.
- 关键字段：
  - `ruleContent.text = "jsoup:#content@css:.inner"`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_PARSER`
- 覆盖能力：
  - complex HTML DSL rejection

---

## S16. Search 阶段忽略元信息样本

- 样本类别：`warning`
- 样本名称：search-stage ignored metadata sample
- 对应测试：
  - `test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields`
- 样本目的：
  - Prove explicitly ignored search-stage metadata remains warning-only.
- 关键字段：
  - `ruleSearch.kind`
  - `ruleSearch.lastChapter`
  - `ruleSearch.wordCount`
  - `ruleSearch.updateTime`
- 预期结果：
  - `is_valid = true`
  - warnings include `LEGADO_IGNORED_FIELD`
- 覆盖能力：
  - search-stage ignored metadata whitelist

---

## S17. Detail 阶段忽略元信息样本

- 样本类别：`warning`
- 样本名称：detail-stage ignored metadata sample
- 对应测试：
  - `test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields`
- 样本目的：
  - Prove explicitly ignored detail-stage metadata remains warning-only.
- 关键字段：
  - `ruleBookInfo.kind`
  - `ruleBookInfo.lastChapter`
  - `ruleBookInfo.wordCount`
  - `ruleBookInfo.updateTime`
- 预期结果：
  - `is_valid = true`
  - warnings include `LEGADO_IGNORED_FIELD`
- 覆盖能力：
  - detail-stage ignored metadata whitelist

---

## S18. `detail_url` 桥接样本

- 样本类别：`success`
- 样本名称：detail URL bridge sample
- 对应测试：
  - `test_validate_legado_import_exposes_detail_url_bridge_placeholder`
- 样本目的：
  - Prove the importer always bridges search-stage detail links into the canonical `{{detail_url}}` request placeholder for the detail stage.
- 关键字段：
  - `ruleSearch.bookUrl`
  - `definition.detail.request.url`
- 预期结果：
  - `is_valid = true`
  - `definition.search.fields.detail_url` exists
  - `definition.detail.request.url = "{{detail_url}}"`
- 覆盖能力：
  - `{{detail_url}}` bridge

---

## S19. `catalog_url` 桥接样本

- 样本类别：`success`
- 样本名称：catalog URL bridge sample
- 对应测试：
  - `test_validate_legado_import_exposes_catalog_url_bridge_placeholder`
- 样本目的：
  - Prove the importer always bridges detail-stage catalog links into the canonical `{{catalog_url}}` request placeholder for the catalog stage.
- 关键字段：
  - `ruleBookInfo.tocUrl`
  - `definition.catalog.request.url`
- 预期结果：
  - `is_valid = true`
  - `definition.detail.fields.catalog_url` exists
  - `definition.catalog.request.url = "{{catalog_url}}"`
- 覆盖能力：
  - `{{catalog_url}}` bridge

---

## S20. `chapter_url` 桥接样本

- 样本类别：`success`
- 样本名称：chapter URL bridge sample
- 对应测试：
  - `test_validate_legado_import_exposes_chapter_url_bridge_placeholder`
- 样本目的：
  - Prove the importer always bridges catalog-stage chapter links into the canonical `{{chapter_url}}` request placeholder for the content stage.
- 关键字段：
  - `ruleToc.chapterUrl`
  - `definition.content.request.url`
- 预期结果：
  - `is_valid = true`
  - `definition.catalog.fields.chapter_url` exists
  - `definition.content.request.url = "{{chapter_url}}"`
- 覆盖能力：
  - `{{chapter_url}}` bridge

---

## S21. Authorization Header 拒绝样本

- 样本类别：`reject`
- 样本名称：Authorization header sample
- 对应测试：
  - `test_validate_legado_import_rejects_authorization_header`
- 样本目的：
  - Prove Authorization headers are rejected during importer validation and do not produce duplicate issues for the same code/path.
- 关键字段：
  - `header.Authorization`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_AUTHORIZATION`
  - only one issue is reported for `header.Authorization`
- 覆盖能力：
  - authorization rejection
  - issue dedupe on same code/path

---

## S22. Dynamic Variable 拒绝样本

- 样本类别：`reject`
- 样本名称：dynamic variable sample
- 对应测试：
  - `test_validate_legado_import_rejects_dynamic_variable_fields`
- 样本目的：
  - Prove dynamic variable declarations stay outside the Phase 2 whitelist.
- 关键字段：
  - `variables`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE`
- 覆盖能力：
  - dynamic variable rejection

---

## S23. Condition DSL 拒绝样本

- 样本类别：`reject`
- 样本名称：condition DSL sample
- 对应测试：
  - `test_validate_legado_import_rejects_condition_dsl`
- 样本目的：
  - Prove conditional DSL fields are rejected instead of being silently tolerated.
- 关键字段：
  - `conditions`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_CONDITION_DSL`
- 覆盖能力：
  - condition DSL rejection

---

## S24. Unsupported Method 拒绝样本

- 样本类别：`reject`
- 样本名称：unsupported method sample
- 对应测试：
  - `test_validate_legado_import_rejects_unsupported_method`
- 样本目的：
  - Prove methods outside `GET/POST` are rejected during importer validation.
- 关键字段：
  - `searchUrl.method = PUT`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_METHOD`
- 覆盖能力：
  - strict HTTP method whitelist

---

## S25. Multi Request 拒绝样本

- 样本类别：`reject`
- 样本名称：multi request sample
- 对应测试：
  - `test_validate_legado_import_rejects_multi_request_structures`
- 样本目的：
  - Prove list-based request chaining stays outside the Phase 2 importer contract and does not emit duplicate issues for the same code/path.
- 关键字段：
  - `requests`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_MULTI_REQUEST`
  - only one issue is reported for `requests`
- 覆盖能力：
  - multi-request rejection
  - issue dedupe on same code/path

---

## S26. Dynamic Request 拒绝样本

- 样本类别：`reject`
- 样本名称：dynamic request sample
- 对应测试：
  - `test_validate_legado_import_rejects_dynamic_request_patterns`
- 样本目的：
  - Prove script-style dynamic request expressions are rejected during importer validation.
- 关键字段：
  - `searchUrl = "@get:..."`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_UNSUPPORTED_DYNAMIC_REQUEST`
- 覆盖能力：
  - dynamic request rejection

---

## S27. Invalid URL 拒绝样本

- 样本类别：`reject`
- 样本名称：invalid base URL sample
- 对应测试：
  - `test_validate_legado_import_rejects_invalid_base_url`
- 样本目的：
  - Prove invalid base URLs fail during canonical validation instead of slipping through importer mapping.
- 关键字段：
  - `bookSourceUrl = "ftp://..."`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_INVALID_URL`
- 覆盖能力：
  - invalid URL rejection

---

## S28. Required Field Missing 拒绝样本

- 样本类别：`reject`
- 样本名称：missing required top-level field sample
- 对应测试：
  - `test_validate_legado_import_rejects_missing_required_stage_definition`
- 样本目的：
  - Prove required top-level stage definitions are enforced during strict whitelist import.
- 关键字段：
  - missing `ruleContent`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_REQUIRED_FIELD_MISSING`
- 覆盖能力：
  - required field enforcement

---

## S29. Mapping Failed 拒绝样本

- 样本类别：`reject`
- 样本名称：invalid stage shape sample
- 对应测试：
  - `test_validate_legado_import_rejects_invalid_stage_shape`
- 样本目的：
  - Prove malformed stage structures fail as mapping errors instead of reaching runtime validation.
- 关键字段：
  - `ruleSearch = "not-an-object"`
- 预期结果：
  - `is_valid = false`
  - fatal error code `LEGADO_MAPPING_FAILED`
- 覆盖能力：
  - mapping failure on invalid object shape

---

## 维护约定

1. 每个新增到测试中的 importer 样本，都应同步登记到本文档。
2. 本文档中的每个样本，都应至少有一条对应回归测试。
3. 若样本类别发生变化（`success` / `warning` / `reject`），必须同时更新：
   - 本样本矩阵
   - 对应测试断言
4. 若新增错误码，并影响到某个样本，必须同时更新：
   - [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
   - [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
   - 本样本矩阵中的受影响条目
