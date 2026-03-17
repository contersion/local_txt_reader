# Legado Import Issue Schema（Phase 2）

本文档定义 Phase 2 静态 importer 的 `errors[]` / `warnings[]` 结构，用于统一：

- API 返回格式
- 前端展示契约
- 调试定位信息
- 测试断言依据
- 向后兼容策略

## 适用范围

适用于以下接口返回的 issue 结构：

- `POST /api/online-sources/import/validate`
- `POST /api/online-sources/import`

以及后续所有基于 Legado importer 的 dry-run / import 类接口。

## 相关文档

- [Legado Phase 2 文档总览](./LEGADO_PHASE2_INDEX.md)
- [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
- [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
- [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
- [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)

## 1. 文档目标

当前 Phase 2 采用“严格白名单 importer”策略。  
导入结果不仅需要告诉调用方“是否成功”，还需要明确：

- 为什么失败
- 失败在哪
- 原始值是什么
- 归一化后变成了什么
- 这是 `hard error` 还是 warning

因此，importer issue 结构需要同时满足：

1. **可读**
   - 人类能直接看懂
2. **可定位**
   - 能定位到 Legado 原始 JSON 的具体路径
3. **可消费**
   - 前端可直接渲染
4. **可测试**
   - 自动化测试可稳定断言
5. **向后兼容**
   - 旧调用方仍可继续使用 `code + message + field`

## 2. Issue 结构总览

每条 issue 当前支持以下字段：

| 字段名 | 类型 | 是否必填 | 说明 |
|---|---|---:|---|
| `code` | `string` | 是 | 旧兼容字段，通常等价于 `error_code` |
| `error_code` | `string` | 是 | 当前规范错误码 |
| `message` | `string` | 是 | 人类可读说明 |
| `severity` | `"error" \| "warning"` | 是 | 问题级别 |
| `field` | `string \| null` | 否 | 旧兼容字段，旧逻辑使用 |
| `source_path` | `string \| null` | 否 | Legado 原始 JSON 路径 |
| `stage` | `"source" \| "search" \| "detail" \| "catalog" \| "content" \| null` | 否 | 所属阶段 |
| `field_name` | `string \| null` | 否 | 逻辑字段名 |
| `raw_value` | `any \| null` | 否 | 原始值摘要 |
| `normalized_value` | `any \| null` | 否 | 归一化后的值摘要 |

## 3. 字段说明

### 3.1 `code`
- 旧兼容字段
- 为了兼容旧调用方保留
- 当前通常与 `error_code` 保持一致

### 3.2 `error_code`
- 当前 importer 的稳定错误码
- 含义由 [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md) 定义

### 3.3 `message`
- 面向人类的可读说明
- 不要求稳定到可编程匹配
- 编程匹配应优先依赖 `error_code`

### 3.4 `severity`
- `error`
  - 表示 `hard error`
  - issue 会出现在 `errors[]`
  - 通常会导致 `is_valid = false`
- `warning`
  - 表示非 fatal 结果
  - issue 会出现在 `warnings[]`
  - 通常不会阻断导入

### 3.5 `field`
- 旧兼容字段
- 当前一般等同于 `source_path`
- 新逻辑应优先看 `source_path`

### 3.6 `source_path`
- Legado 原始 JSON 中的路径
- 示例：
  - `ruleContent.content`
  - `header.Cookie`
  - `bookSourceGroup`

### 3.7 `stage`
- 用于指出 issue 所属的 importer 语义阶段
- 允许值：
  - `source`
  - `search`
  - `detail`
  - `catalog`
  - `content`

### 3.8 `field_name`
- 逻辑字段名摘要
- 示例：
  - `content`
  - `Cookie`
  - `bookSourceGroup`

### 3.9 `raw_value`
- 原始值摘要
- 用于帮助快速定位问题来源
- 不承诺完整保留原始输入结构

### 3.10 `normalized_value`
- 归一化后的值摘要
- 只在当前实现确实发生了静态归一化、且结果对调试有帮助时返回
- 若没有合适摘要，则返回 `null`

## 4. 结果解释规则

### 4.1 `errors[]`
- 只包含 `severity = "error"` 的 issue
- 代表 `hard error`
- 这些 issue 会阻断当前 importer validate / import 成功

### 4.2 `warnings[]`
- 只包含 `severity = "warning"` 的 issue
- 代表非 fatal 问题
- 常见于：
  - `warning + ignore`
  - 受控静态归一化

### 4.3 `ignored_fields`
- 只记录被 `warning + ignore` 的原始路径
- 与 `warnings[]` 中的对应 issue 配套使用

### 4.4 `unsupported_fields`
- 只记录导致 `hard error` 的原始路径
- 与 `errors[]` 中的对应 issue 配套使用

### 4.5 duplicate issue 约定
- 当前 importer 不应为同一个 `error_code + source_path` 重复输出多条 issue
- 如果多个校验分支指向同一个问题，应保留一条最具代表性的 issue
- `message` 的差异本身不应成为重复输出的理由
- 相关回归样本与测试：
  - `S21` -> `test_validate_legado_import_rejects_authorization_header`
  - `S25` -> `test_validate_legado_import_rejects_multi_request_structures`

## 5. 样本 -> issue 结构示例

以下示例只使用当前仓库中已经存在的真实样本、真实错误码和真实测试函数。

### 5.1 warning 示例：ignored field

- 样本：
  - `S3`
  - `S12`
  - `S16`
  - `S17`
- 参考测试：
  - `test_validate_legado_import_warns_and_ignores_display_fields`
  - `test_validate_legado_import_warns_and_ignores_source_level_metadata_fields`
  - `test_validate_legado_import_warns_and_ignores_search_stage_metadata_fields`
  - `test_validate_legado_import_warns_and_ignores_detail_stage_metadata_fields`
- 对应错误码：
  - `LEGADO_IGNORED_FIELD`

示例：

```json
{
  "code": "LEGADO_IGNORED_FIELD",
  "error_code": "LEGADO_IGNORED_FIELD",
  "message": "bookSourceGroup is ignored during strict whitelist import",
  "severity": "warning",
  "field": "bookSourceGroup",
  "source_path": "bookSourceGroup",
  "stage": "source",
  "field_name": "bookSourceGroup",
  "raw_value": "Group A",
  "normalized_value": null
}
```

### 5.2 warning 示例：`selector@html` 归一化

- 样本：
  - `S11`
- 参考测试：
  - `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`
- 对应错误码：
  - `LEGADO_CSS_HTML_NORMALIZED`

示例：

```json
{
  "code": "LEGADO_CSS_HTML_NORMALIZED",
  "error_code": "LEGADO_CSS_HTML_NORMALIZED",
  "message": "ruleContent.text uses @html and was normalized to the current CSS text-compatible form",
  "severity": "warning",
  "field": "ruleContent.text",
  "source_path": "ruleContent.text",
  "stage": "content",
  "field_name": "text",
  "raw_value": "jsoup:#content@html",
  "normalized_value": {
    "parser": "css",
    "expr": "#content"
  }
}
```

### 5.3 warning 示例：alias 归一化

当前**无独立 issue 示例**。

说明：
- 例如 `{{key}} -> {{keyword}}`、`json: -> jsonpath`、`jsoup: -> css` 这类 alias 归一化目前有真实样本和测试覆盖
- 但当前实现不会专门为这些 alias 归一化单独生成 warning issue
- 相关样本与测试可参考：
  - `S2`
  - `S13`
  - `test_validate_legado_import_supports_common_aliases_and_css_jsoup_forms`
  - `test_validate_legado_import_accepts_absolute_search_url`

### 5.4 reject 示例：JS

- 样本：
  - `S4`
- 参考测试：
  - `test_validate_legado_import_rejects_js`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_JS`

示例：

```json
{
  "code": "LEGADO_UNSUPPORTED_JS",
  "error_code": "LEGADO_UNSUPPORTED_JS",
  "message": "ruleContent.content contains unsupported pattern: @js:",
  "severity": "error",
  "field": "ruleContent.content",
  "source_path": "ruleContent.content",
  "stage": "content",
  "field_name": "content",
  "raw_value": "@js:result",
  "normalized_value": null
}
```

### 5.5 reject 示例：Cookie

- 样本：
  - `S5`
- 参考测试：
  - `test_validate_legado_import_rejects_cookie_and_login_state`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_COOKIE`

示例：

```json
{
  "code": "LEGADO_UNSUPPORTED_COOKIE",
  "error_code": "LEGADO_UNSUPPORTED_COOKIE",
  "message": "Cookie headers are not supported",
  "severity": "error",
  "field": "header.Cookie",
  "source_path": "header.Cookie",
  "stage": "source",
  "field_name": "Cookie",
  "raw_value": "sid=1",
  "normalized_value": null
}
```

### 5.6 reject 示例：webView

- 样本：
  - `S6`
- 参考测试：
  - `test_validate_legado_import_rejects_webview_and_proxy`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_WEBVIEW`

示例：

```json
{
  "code": "LEGADO_UNSUPPORTED_WEBVIEW",
  "error_code": "LEGADO_UNSUPPORTED_WEBVIEW",
  "message": "webView is not supported in Phase 2 whitelist import",
  "severity": "error",
  "field": "webView",
  "source_path": "webView",
  "stage": "source",
  "field_name": "webView",
  "raw_value": true,
  "normalized_value": null
}
```

### 5.7 reject 示例：charset override

- 样本：
  - `S7`
- 参考测试：
  - `test_validate_legado_import_rejects_charset_override`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_CHARSET_OVERRIDE`

示例：

```json
{
  "code": "LEGADO_UNSUPPORTED_CHARSET_OVERRIDE",
  "error_code": "LEGADO_UNSUPPORTED_CHARSET_OVERRIDE",
  "message": "charset is not supported in Phase 2 whitelist import",
  "severity": "error",
  "field": "charset",
  "source_path": "charset",
  "stage": "source",
  "field_name": "charset",
  "raw_value": "gbk",
  "normalized_value": null
}
```

### 5.8 reject 示例：unsupported parser

- 样本：
  - `S14`
  - `S15`
- 参考测试：
  - `test_validate_legado_import_rejects_unsupported_parser_prefix`
  - `test_validate_legado_import_rejects_complex_html_dsl`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_PARSER`

示例 1：未知 parser 前缀

```json
{
  "code": "LEGADO_UNSUPPORTED_PARSER",
  "error_code": "LEGADO_UNSUPPORTED_PARSER",
  "message": "ruleSearch.bookList does not use a supported parser prefix or expression",
  "severity": "error",
  "field": "ruleSearch.bookList",
  "source_path": "ruleSearch.bookList",
  "stage": "search",
  "field_name": "bookList",
  "raw_value": "jq:.result-item",
  "normalized_value": null
}
```

示例 2：复杂 HTML DSL

```json
{
  "code": "LEGADO_UNSUPPORTED_PARSER",
  "error_code": "LEGADO_UNSUPPORTED_PARSER",
  "message": "ruleContent.text uses unsupported nested parser syntax: css:.inner",
  "severity": "error",
  "field": "ruleContent.text",
  "source_path": "ruleContent.text",
  "stage": "content",
  "field_name": "text",
  "raw_value": "jsoup:#content@css:.inner",
  "normalized_value": null
}
```

### 5.9 bridge / normalization 相关说明

当前 bridge placeholder 已有真实独立样本，但**没有直接 issue 示例**。

原因：
- `{{detail_url}}`、`{{catalog_url}}`、`{{chapter_url}}` 是成功桥接行为
- 当前实现会把它们静态写入 canonical request URL
- 这类成功桥接本身不会生成 warning issue，也不会生成 error issue

相关样本与测试：
- `S18` -> `test_validate_legado_import_exposes_detail_url_bridge_placeholder`
- `S19` -> `test_validate_legado_import_exposes_catalog_url_bridge_placeholder`
- `S20` -> `test_validate_legado_import_exposes_chapter_url_bridge_placeholder`

### 5.10 reject 示例：Authorization header

- 样本：
  - `S21`
- 参考测试：
  - `test_validate_legado_import_rejects_authorization_header`
- 对应错误码：
  - `LEGADO_UNSUPPORTED_AUTHORIZATION`

示例：

```json
{
  "code": "LEGADO_UNSUPPORTED_AUTHORIZATION",
  "error_code": "LEGADO_UNSUPPORTED_AUTHORIZATION",
  "message": "Authorization headers are not supported",
  "severity": "error",
  "field": "header.Authorization",
  "source_path": "header.Authorization",
  "stage": "source",
  "field_name": "Authorization",
  "raw_value": "Bearer secret-token",
  "normalized_value": null
}
```

## 6. 向后兼容约定

- 老调用方仍可继续只读取：
  - `code`
  - `message`
  - `field`
- 新调用方应优先使用：
  - `error_code`
  - `severity`
  - `source_path`
  - `stage`
  - `field_name`
  - `raw_value`
  - `normalized_value`

## 7. 维护约定

1. 若新增 issue 字段，必须同步更新本文档
2. 若新增错误码，必须同步更新：
   - [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
   - [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
3. 若新增样本并影响 issue 结构示例，必须同步更新：
   - [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
   - 本文档的“样本 -> issue 结构示例”小节
