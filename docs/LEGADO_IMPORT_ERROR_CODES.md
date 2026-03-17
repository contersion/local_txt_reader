# Legado Import 错误码（Phase 2）

本文档定义 Phase 2 静态 importer 使用的稳定错误码与 warning 码。

## 适用范围

适用于以下接口：

- `POST /api/online-sources/import/validate`
- `POST /api/online-sources/import`

本阶段仍然只覆盖静态 importer，不包含高兼容运行时。

## 相关文档

- [Legado Phase 2 文档总览](./LEGADO_PHASE2_INDEX.md)
- [Legado 字段映射规范（Phase 2）](./LEGADO_FIELD_MAPPING_PHASE2.md)
- [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
- [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
- [Legado Import Issue Schema（Phase 2）](./LEGADO_IMPORT_ISSUE_SCHEMA.md)

## 错误码表

| 错误码 | 含义 | 触发条件 | 是否 hard error | 建议处理方式 |
| --- | --- | --- | --- | --- |
| `LEGADO_UNSUPPORTED_JS` | JavaScript 执行不受支持 | `@js:`、`<js>`、`javascript:`、`eval(`、`function(`、`=>`、`js/script/scripts` 字段 | 是 | 去掉 JS 规则，改写为静态 CSS / JSONPath / XPath / regex |
| `LEGADO_UNSUPPORTED_COOKIE` | Cookie 请求不受支持 | `Cookie` header 或 cookie 字段 | 是 | 移除 Cookie 依赖，保持无状态请求 |
| `LEGADO_UNSUPPORTED_AUTHORIZATION` | Authorization header 不受支持 | `Authorization` header 或相关字段 | 是 | 移除授权 header；需要鉴权的书源不属于当前阶段 |
| `LEGADO_UNSUPPORTED_LOGIN_STATE` | 登录态 / session / token 流程不受支持 | `login`、`loginUrl`、`session`、`token` 字段 | 是 | 排除依赖登录态的书源 |
| `LEGADO_UNSUPPORTED_WEBVIEW` | WebView / 浏览器态不受支持 | `webView` 字段 | 是 | 仅保留普通 HTTP 书源 |
| `LEGADO_UNSUPPORTED_PROXY` | 代理执行不受支持 | `proxy`、`proxyUrl` 字段 | 是 | 去掉 proxy 依赖 |
| `LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE` | 动态变量求值不受支持 | `variable`、`variables` 字段 | 是 | 只保留固定白名单占位符 |
| `LEGADO_UNSUPPORTED_CONDITION_DSL` | 条件 DSL 不受支持 | `condition`、`conditions` 字段 | 是 | 展平成静态规则，或直接拒绝 |
| `LEGADO_UNSUPPORTED_CHARSET_OVERRIDE` | 显式 charset override 不受支持 | `charset` 字段 | 是 | 让运行时使用正常 HTTP 解码，不在 importer 强制 charset |
| `LEGADO_UNSUPPORTED_REPLACE_DSL` | 自定义 replace / clean DSL 不受支持 | `replace`、`replaceRule`、`replaceRegex`、`replaceList` | 是 | 仅依赖内置 `_clean_text()` |
| `LEGADO_UNSUPPORTED_PARSER` | parser 超出白名单 | 未知 parser 前缀、未知 parser 结构、复杂 HTML DSL | 是 | 仅使用 `css/jsoup/jsonpath/json/xpath/regex` |
| `LEGADO_UNSUPPORTED_METHOD` | HTTP method 超出白名单 | 非 `GET/POST` | 是 | 改写为 `GET` 或 `POST` |
| `LEGADO_UNSUPPORTED_PLACEHOLDER` | 占位符超出白名单 | 除 `{{key}}` / `{{page}}` 外的原始占位符 | 是 | 替换为支持的占位符 |
| `LEGADO_UNSUPPORTED_MULTI_REQUEST` | 多请求链式执行不受支持 | `requests`、`steps`、`pipeline`、列表链式结构、next-step 字段 | 是 | 保持每阶段单请求 |
| `LEGADO_UNSUPPORTED_DYNAMIC_REQUEST` | 动态脚本式请求不受支持 | `@put`、动态 `@get`、`java.put`、`java.get` | 是 | 仅使用静态 `GET/POST` |
| `LEGADO_UNSUPPORTED_FIELD` | 字段不在 importer 白名单内 | 未知执行字段或未批准 alias | 是 | 显式补 mapper alias，或移除字段 |
| `LEGADO_INVALID_URL` | URL 无法静态归一化 | base URL 非法、阶段 URL 非法 | 是 | 改成绝对或可归一化的相对 HTTP URL |
| `LEGADO_REQUIRED_FIELD_MISSING` | canonical 必填字段缺失 | top-level 或 stage 必填字段在映射后缺失 | 是 | 补齐对应字段或 alias |
| `LEGADO_MAPPING_FAILED` | 静态映射结构失败 | 请求 JSON 结构坏、body 结构坏、对象形状不合法 | 是 | 先修正源结构 |
| `LEGADO_IGNORED_FIELD` | 明确忽略的展示/元信息字段 | `bookSourceGroup`、`customOrder`、`weight` 等明确 ignore 白名单字段 | 否 | 可忽略，不阻断导入 |
| `LEGADO_CSS_HTML_NORMALIZED` | `selector@html` 被受控静态归一化 | 支持的 CSS / JSoup `@html` 写法 | 否 | 若内容格式敏感，人工复核归一化结果 |

## 说明

- `hard error` 会出现在 `errors[]` 中，并使 `is_valid = false`
- 非 fatal 结果会出现在 `warnings[]` 中，并保持 `is_valid = true`
- `warning + ignore` 只适用于字段映射规范中明确列出的 ignore 白名单字段
- `unsupported_fields` 记录导致 hard error 的原始路径
- `ignored_fields` 记录被 warning + ignore 的原始路径
