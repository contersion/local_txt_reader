# Legado 字段映射规范（Phase 2）

本文档定义当前项目在 **Phase 2：Legado 静态 importer 第一阶段** 下，对 Legado 字段的支持范围、映射关系、限制条件与拒绝原因。

它描述的是当前阅读3（Legado）兼容工作中的静态 importer 子集边界，而不是高兼容运行时。

## 目标

本阶段目标不是高兼容运行时，而是：

- 严格白名单导入
- 仅支持可静态映射到现有 `OnlineSourceDefinition` 的字段
- 导入成功后的书源继续走现有 Phase 1 执行链
- 对不支持的执行语义字段直接报错
- 对纯展示字段采用 `warning + ignore`

## 相关文档

- [Legado Phase 2 文档总览](./LEGADO_PHASE2_INDEX.md)
- [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
- [Legado Import 样本矩阵（Phase 2）](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
- [Legado Import Traceability 索引（Phase 2）](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
- [Legado Import Issue Schema（Phase 2）](./LEGADO_IMPORT_ISSUE_SCHEMA.md)

---

## 兼容原则

### 支持原则
只有满足以下条件的字段才允许导入：

1. 能静态映射到当前 canonical source definition
2. 不引入新的运行时概念
3. 不依赖脚本执行、浏览器态、会话态、变量求值器、多步编排
4. 能继续复用现有：
   - `source_validator`
   - `source_normalizer`
   - `fetch_service`
   - `parser_engine`
   - `content_parse_service`
   - `source_engine`

### 拒绝原则
以下字段或能力必须在 importer / validator 阶段直接报错：

- JS / `@js:` / `<js>`
- Cookie / Authorization / 登录态
- `webView`
- `proxy`
- `@put` / 动态 `@get` / `java.put` / `java.get`
- 多请求链式执行
- 复杂变量系统
- 复杂条件 DSL
- 显式 `charset` 覆盖
- 自定义 replace / 净化 DSL
- 白名单外 parser
- 白名单外占位符

### 忽略原则
只有**明确列出的字段**才允许：
- `warning + ignore`

其余未知字段默认：
- `hard error`

不允许把未知字段自动归为“展示字段”。

---

## 1. 书源基础信息字段

| Legado 原字段 | 所属阶段 | 是否支持 | 映射目标 | 说明 | 不支持原因 / 备注 |
|---|---|---:|---|---|---|
| `bookSourceName` | source | 支持 | `name` | 书源名称 | - |
| `bookSourceComment` | source | 支持 | `description` | 仅接受纯文本 | 非纯文本内容应归一化或报错 |
| `bookSourceUrl` | source | 支持 | `base_url` | 站点根地址 | 必须可归一化为合法 URL |
| `enabled` | source | 支持 | `enabled` | 启用状态 | - |
| `bookSourceGroup` | source | warning + ignore | - | 纯展示字段 | 当前不参与执行 |
| `bookSourceType` | source | warning + ignore | - | 元信息字段 | 当前不参与执行 |
| `customOrder` | source | warning + ignore | - | 排序/展示字段 | 当前不参与执行 |
| `weight` | source | warning + ignore | - | 排序/展示字段 | 当前不参与执行 |
| `lastUpdateTime` | source | warning + ignore | - | 展示字段 | 当前不参与执行 |
| `respondTime` | source | warning + ignore | - | 展示字段 | 当前不参与执行 |

---

## 2. 请求层字段

| Legado 原字段 | 所属阶段 | 是否支持 | 映射目标 | 说明 | 不支持原因 / 备注 |
|---|---|---:|---|---|---|
| `searchUrl` | search | 支持 | `definition.search.request` | 仅限可静态拆成单请求 | 不支持多请求链 |
| `method` | 各阶段 | 支持（仅 GET/POST） | `request.method` | 只支持 `GET` / `POST` | 其他 method 直接报错 |
| `header` | 各阶段 | 支持（静态） | `request.headers` | 仅静态键值对 | Cookie/Authorization 报错 |
| `body` | 各阶段 | 支持（静态） | `request.body` | 仅静态键值对 | 动态 body 逻辑不支持 |
| 相对 URL | 各阶段 | 支持 | `request.url` | 允许拼接 base_url | 必须能静态归一化 |
| 绝对 URL | 各阶段 | 支持 | `request.url` | 允许 `http/https` | 非法 scheme 报错 |
| `charset` | 各阶段 | 不支持 | - | 当前无 request.charset 执行槽位 | 直接报错 |
| `proxy` | 各阶段 | 不支持 | - | 当前无代理执行层 | 直接报错 |
| `webView` | 各阶段 | 不支持 | - | 当前无浏览器态执行层 | 直接报错 |

---

## 3. 占位符支持表

| Legado 占位符 | 是否支持 | 归一化结果 | 说明 |
|---|---:|---|---|
| `{{key}}` | 支持 | `{{keyword}}` | 搜索关键字别名 |
| `{{page}}` | 支持 | `{{page}}` | 分页占位符 |
| `{{detail_url}}` | 支持 | `{{detail_url}}` | 内部 canonical |
| `{{catalog_url}}` | 支持 | `{{catalog_url}}` | 内部 canonical |
| `{{chapter_url}}` | 支持 | `{{chapter_url}}` | 内部 canonical |

### 3.1 白名单外占位符
任何不在上述列表中的占位符：
- 一律报错
- 不允许静默忽略
- 不允许导入后运行时兜底

---

## 4. Parser 支持表

| Legado 写法 | 是否支持 | 归一化 parser | 说明 |
|---|---:|---|---|
| `css:` | 支持 | `css` | 标准 CSS |
| `jsoup:` | 支持 | `css` | 与 CSS 统一归一化 |
| `jsonpath:` | 支持 | `jsonpath` | 标准 JSONPath |
| `json:` | 支持 | `jsonpath` | 作为 JSONPath 别名 |
| `xpath:` | 支持 | `xpath` | 标准 XPath |
| `regex:` | 支持 | `regex` | 标准 regex |
| 白名单外 parser | 不支持 | - | 直接报错 |

---

## 5. CSS / JSoup 兼容写法

| 原写法 | 是否支持 | 归一化结果 | 说明 |
|---|---:|---|---|
| `selector@text` | 支持 | `parser=css, expr=selector` | 文本提取，`attr` 可省略 |
| `selector@href` | 支持 | `parser=css, expr=selector, attr=href` | 属性提取 |
| `selector@src` | 支持 | `parser=css, expr=selector, attr=src` | 属性提取 |
| `selector@html` | 支持（受控） | 静态归一化 | 返回 `LEGADO_CSS_HTML_NORMALIZED` warning |
| 复杂 HTML DSL | 不支持 | - | 不引入运行时 HTML 处理 DSL |

---

## 6. 四阶段字段映射表

### 6.1 搜索阶段（search）

| Legado 字段 | alias | 是否支持 | 映射目标 | 必填 |
|---|---|---:|---|---:|
| `bookList` | `list` | 支持 | `definition.search.list_selector` | 否 |
| `name` | `bookName` | 支持 | `definition.search.fields.title` | 是 |
| `bookUrl` | `url` | 支持 | `definition.search.fields.detail_url` | 是 |
| `author` | - | 支持 | `definition.search.fields.author` | 否 |
| `intro` | `desc`, `description` | 支持 | `definition.search.fields.description` | 否 |
| `coverUrl` | `cover` | 支持 | `definition.search.fields.cover_url` | 否 |
| `bookId` | `id` | 支持 | `definition.search.fields.remote_book_id` | 否 |
| `kind` | - | warning + ignore | - | 显式列入忽略白名单 |
| `lastChapter` | - | warning + ignore | - | 显式列入忽略白名单 |
| `wordCount` | - | warning + ignore | - | 显式列入忽略白名单 |
| `updateTime` | - | warning + ignore | - | 显式列入忽略白名单 |

### 6.2 详情阶段（detail）

| Legado 字段 | alias | 是否支持 | 映射目标 | 必填 |
|---|---|---:|---|---:|
| `name` | `bookName` | 支持 | `definition.detail.fields.title` | 是 |
| `author` | - | 支持 | `definition.detail.fields.author` | 否 |
| `intro` | `desc`, `description` | 支持 | `definition.detail.fields.description` | 否 |
| `coverUrl` | `cover` | 支持 | `definition.detail.fields.cover_url` | 否 |
| `tocUrl` | `catalogUrl`, `chapterUrl` | 支持 | `definition.detail.fields.catalog_url` | 是 |
| `kind` | - | warning + ignore | - | 显式列入忽略白名单 |
| `lastChapter` | - | warning + ignore | - | 显式列入忽略白名单 |
| `wordCount` | - | warning + ignore | - | 显式列入忽略白名单 |
| `updateTime` | - | warning + ignore | - | 显式列入忽略白名单 |

### 6.3 目录阶段（catalog）

| Legado 字段 | alias | 是否支持 | 映射目标 | 必填 |
|---|---|---:|---|---:|
| `chapterList` | `list` | 支持 | `definition.catalog.list_selector` | 否 |
| `chapterName` | `name` | 支持 | `definition.catalog.fields.chapter_title` | 是 |
| `chapterUrl` | `url` | 支持 | `definition.catalog.fields.chapter_url` | 是 |

### 6.4 正文阶段（content）

| Legado 字段 | alias | 是否支持 | 映射目标 | 必填 |
|---|---|---:|---|---:|
| `content` | `text`, `body` | 支持 | `definition.content.fields.content` | 是 |

---

## 7. 明确拒绝的字段/能力

| 字段 / 能力 | 是否支持 | 处理方式 | 原因 |
|---|---:|---|---|
| `@js:` | 不支持 | hard error | 需要脚本执行器 |
| `<js>...</js>` | 不支持 | hard error | 需要脚本执行器 |
| `javascript:` | 不支持 | hard error | 需要脚本执行器 |
| `eval(` / `function(` / `=>` | 不支持 | hard error | 需要脚本执行器 |
| `js/script/scripts` 字段 | 不支持 | hard error | 需要脚本执行器 |
| `Cookie` | 不支持 | hard error | 需要会话态 |
| `Authorization` | 不支持 | hard error | 需要会话态 |
| 登录态 / session / token | 不支持 | hard error | 当前无会话管理层 |
| `webView` | 不支持 | hard error | 当前无浏览器执行环境 |
| `proxy` | 不支持 | hard error | 当前无代理执行层 |
| `@put` / 动态 `@get` | 不支持 | hard error | 当前无变量引擎 |
| `java.put` / `java.get` | 不支持 | hard error | 当前无变量引擎 |
| `requests / steps / pipeline` | 不支持 | hard error | 当前单阶段单请求 |
| 复杂变量系统 | 不支持 | hard error | 当前无变量求值器 |
| 条件 DSL | 不支持 | hard error | 当前无表达式执行层 |
| 显式 `charset` 覆盖 | 不支持 | hard error | 当前无 request.charset 槽位 |
| 自定义 replace / 净化 DSL | 不支持 | hard error | 当前仅支持固定 `_clean_text()` |

---

## 8. Warning + Ignore 字段

以下字段如出现，可：
- 返回 warning
- 记录到 `ignored_fields`
- 不参与执行

### 8.1 仅允许以下明确列出的字段

| 字段 | 行为 | 说明 |
|---|---|---|
| `bookSourceGroup` | warning + ignore | 仅展示用途 |
| `bookSourceType` | warning + ignore | 元信息字段 |
| `customOrder` | warning + ignore | 当前不参与执行 |
| `weight` | warning + ignore | 当前不参与执行 |
| `lastUpdateTime` | warning + ignore | 当前不参与执行 |
| `respondTime` | warning + ignore | 当前不参与执行 |
| `ruleSearch.kind` | warning + ignore | 显式列入忽略白名单 |
| `ruleSearch.lastChapter` | warning + ignore | 显式列入忽略白名单 |
| `ruleSearch.wordCount` | warning + ignore | 显式列入忽略白名单 |
| `ruleSearch.updateTime` | warning + ignore | 显式列入忽略白名单 |
| `ruleBookInfo.kind` | warning + ignore | 显式列入忽略白名单 |
| `ruleBookInfo.lastChapter` | warning + ignore | 显式列入忽略白名单 |
| `ruleBookInfo.wordCount` | warning + ignore | 显式列入忽略白名单 |
| `ruleBookInfo.updateTime` | warning + ignore | 显式列入忽略白名单 |

### 8.2 未知字段默认策略
任何**不在支持表中，也不在上表忽略白名单中**的字段：
- 一律 `hard error`
- 错误码：`LEGADO_UNSUPPORTED_FIELD`
- 不允许自动归为“展示字段”

---

## 9. 导入结果解释规则

### 9.1 `is_valid = true`
表示：
- 当前 source 落在 Phase 2 白名单内
- 已成功映射为 `OnlineSourceDefinition`
- 可以继续走现有 discovery 执行链

### 9.2 `is_valid = false`
表示：
- 存在 hard error
- 当前 source 不应导入
- 必须先移除或修改不支持能力

### 9.3 `warnings`
表示：
- 存在被忽略字段
- 或存在受控静态归一化
- 但不阻断导入

---

## 10. 维护约定

1. 新增 alias 时，必须同步更新本文档
2. 新增 error code 时，必须同步更新：
   - [Legado Import 错误码（Phase 2）](./LEGADO_IMPORT_ERROR_CODES.md)
   - 本文档中相关字段说明
3. 新增支持字段前，必须先判断：
   - 是否仍可静态映射
   - 是否会引入新的运行时概念
4. 若需要 JS / Cookie / 登录态 / webView，必须进入后续高风险阶段，不得在 Phase 2 白名单中偷偷扩进去
