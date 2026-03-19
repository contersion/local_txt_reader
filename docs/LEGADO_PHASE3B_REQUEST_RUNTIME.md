# Legado Phase 3-B Request Runtime Design

## 1. 文档定位

本文档只服务于 **Phase 3-B 强约束设计阶段**。

当前最新轮次进一步固定为：

- `Phase 3-B.8`：detector live 接缝决策轮
- 默认结论：只做决策、文档、Traceability、错误码分层与测试规划
- 默认不改代码

当前目标不是实现复杂请求运行时，而是：

- 扫描当前请求执行链
- 划清复杂请求问题边界
- 设计能力分层与模块接缝
- 设计错误码与测试规划
- 明确哪些能力必须后置，防止过早实装

当前默认结论：

> 本轮停留在设计层已经足够推进项目，不需要进入 Phase 3-B 实装。

本轮四个关键决策的完整方案比较，统一记录于：

- `docs/LEGADO_PHASE3B_DECISIONS.md`

在当前轮次之后，仓库已额外完成：

- `Phase 3-B.2`：最小 preflight 实装
- `Phase 3-B.3`：generic response_guard 最小分类实装
- `Phase 3-B.4`：response_guard 扩展前决策轮（文档/决策层）
- `Phase 3-B.5`：detector / anti-bot 边界设计轮（文档/决策层）
- `Phase 3-B.6`：detector 最小静态分类骨架决策轮（文档/决策层）
- `Phase 3-B.7`：detector 最小静态分类骨架实现（纯内部、纯离线）

但该实现仍然严格限定在：

- L2 request descriptor / runtime schema
- 发请求前的静态校验
- 3 个最小错误码分类
- L3 中最保守的 generic response classification：
  - timeout
  - HTTP 429

并且仍然 **不等于**：

- detector / anti-bot 实装
- suspicious HTML / challenge / gateway detection
- JS / WebView / browser fallback 实装
- detector live runtime 接入

## 2. 当前仓库请求执行链扫描结论

当前在线请求执行链为：

1. `router`
   - `backend/app/routers/online_discovery.py`
2. `source_engine`
   - 负责 stage request 渲染与阶段编排
3. `request_profile_service`
   - 当前只负责最小 headers/query/body/cookies 组装与 session/auth skeleton 校验
4. `fetch_service`
   - 负责真实 HTTP 请求执行、大小限制、状态码与内容类型基础校验
5. `parser_engine`
   - 负责 css/jsonpath/xpath/regex 提取
6. `content_parse_service`
   - 负责 search/detail/catalog/content 的结构化解析与正文清洗

### 2.1 当前已经覆盖的能力

- 无状态 GET/POST
- 静态 query/body/header
- 基础 cookies 注入挂点
- 基础 session/auth skeleton 校验
- 基础 timeout / invalid URL / response type mismatch 错误

### 2.2 当前明确没有覆盖的能力

- request body mode 区分
  - form / json / raw text / multipart 的显式模式化描述
- header template / nonce / timestamp / signature placeholder
- retry / redirect / rate limit 的分类策略
- suspicious HTML / anti-bot gateway / challenge 检测
- JS 参与的签名或变量求值
- browser/WebView 依赖的执行能力

## 3. 核心判断：为什么本轮默认应停在设计层

当前仓库已经足以回答 Phase 3-B 的关键架构问题：

- `source_engine -> request_profile_service -> fetch_service` 的接缝已经存在
- `fetch_service` 已经是独立的最小传输层
- `request_profile_service` 已经证明“复杂请求能力不应直接塞进 router 或 parser”
- `router` 与前端当前完全不感知新 runtime 参数，公共 API 仍然稳定

因此，本轮继续写代码并不是“推进设计所必需”的条件。

本轮如果只完成：

- 问题分层
- 模块设计
- 错误码分层
- Traceability
- 测试规划

就已经足够为未来 3-B 实装提供依据。

换句话说：

> 现阶段缺的不是骨架，而是对“什么可以做成请求描述问题、什么只能做成识别问题、什么必须延后”的清晰边界。

### 3.1 本轮是否需要落代码

按当前仓库证据，本轮判断应分成两个步骤：

#### Step 1：只做文档与决策是否已经足够

结论：**足够**

原因：

- 现有 `source_engine -> request_profile_service -> fetch_service` 接缝已经足以支撑结构决策
- 当前最危险的是“语义没钉死”，不是“少一个运行时骨架”
- 本轮四个问题都可以只靠现有代码与文档得出明确结论

#### Step 2：若主张必须落代码，是否已有充分证明

结论：**没有充分证明**

当前没有证据表明：

- 不落代码会阻塞下一轮
- 需要落的代码已经小到不能再小
- 新增 enum/type/schema 不会被误解为 3-B 已实装

因此本轮默认停在文档层。

## 4. 问题分层

### L0：普通 HTTP

范围：

- 无状态 GET / POST
- 普通 query/body/header
- 普通 HTML / JSON 响应

当前项目状态：

- 已实现
- 已由现有 online discovery 主链稳定支撑

本轮动作：

- 只复盘，不新增实现

### L1：Session / Cookie / Header 注入

范围：

- session context
- cookie 注入
- auth config skeleton
- 内部可选 runtime hook

当前项目状态：

- 已在 3-A / 3-A.1 建骨架
- 仍未正式支持登录型书源

本轮动作：

- 只承认其为 skeleton，不向上扩写为“正式支持”

### L2：请求描述与参数装配

范围：

- body mode 描述
  - form / json / raw
- query/body/header 组合策略
- request profile
- header template
- nonce / timestamp / 固定签名占位

当前项目状态：

- `request_profile_service` 只覆盖了极小子集
- `OnlineRequestDefinition` 目前只有 `headers/query/body: dict[str, str]`
- 还没有 body mode、header template、signature placeholder 的稳定 schema

本轮动作：

- 只做设计
- 不引入新的执行逻辑

### L3：请求行为控制与风险响应识别

范围：

- timeout 分类
- retry 分类
- redirect policy
- rate limit 分类
- suspicious HTML 响应识别
- challenge / anti-bot gateway 检测

当前项目状态：

- 只有最基础的 timeout / invalid URL / response type mismatch 报错
- 没有正式的 response classification 层

本轮动作：

- 只设计“识别与分类”
- 不设计“绕过与恢复”

### L4：需要 JS

范围：

- JS 表达式
- 动态签名
- 页面态变量求值

当前项目状态：

- 未实现
- 明确不属于 3-B 当前实装范围

本轮动作：

- 只标记为 `deferred to 3-C`

### L5：需要浏览器态

范围：

- 浏览器指纹
- WebView / browser challenge
- 人机验证 / 交互认证

当前项目状态：

- 未实现
- 明确不属于 3-B 当前实装范围

本轮动作：

- 只标记为 `deferred to 3-D`

## 5. “识别”与“绕过”的边界

这是 Phase 3-B 最容易失控的地方，必须单独写清楚：

### 允许设计的内容

- 识别 rate limit 响应
- 识别 suspicious HTML
- 识别 anti-bot gateway
- 识别 challenge 页面
- 识别“需要 JS”或“需要浏览器态”的失败类型

### 明确不允许在本轮实现的内容

- 绕过 challenge
- 自动重试到成功
- 自动刷新 cookie
- 自动生成动态签名
- 自动执行 JS
- 自动切换浏览器态

结论：

> 识别问题不等于解决问题。Phase 3-B 当前设计阶段只能回答“这是什么问题”，不能承诺“系统已经会绕过这个问题”。

## 6. 模块接缝设计

### 6.1 应复用的现有模块

- `source_engine.py`
  - 继续做阶段编排，不重写
- `request_profile_service.py`
  - 继续做请求画像装配，不扩写成复杂执行引擎
- `fetch_service.py`
  - 保持为叶子传输层，不塞入复杂策略
- `parser_engine.py`
  - 继续只做内容提取
- `content_parse_service.py`
  - 继续只做结构化解析与正文清洗

### 6.2 设计中的新增模块

以下为 **设计中的模块边界**，当前仓库尚未实现：

- `request_runtime_schema`
  - 描述 body mode、header template、preflight/postflight policy
- `request_runtime_coordinator`
  - 位于 `source_engine` 与 `fetch_service` 之间，负责运行时调度
- `request_body_encoder`
  - 负责 form/json/raw body 的模式化编码
- `response_guard_service`
  - 负责响应分类，而不是内容解析
- `anti_bot_detector`
  - 只负责 detection，不负责 bypass

### 6.2.1 3-B.1 决策固定后的模块归属

本轮四个关键决策固定后，应把模块职责理解为：

- `request_runtime_schema`
  - 负责内部 `request descriptor`
  - 负责 `RequestBodyMode`
  - 负责 header template / signature placeholder 的静态建模
- `request_profile_service`
  - 继续负责 request profile 组装
  - 在 3-B 首个最小实装阶段，只允许加入轻量 preflight helper
  - 当前不升级为独立 template engine
- `request_body_encoder`
  - 未来负责 `query / form / json / raw` 的编码分流
  - 当前未实现
- `response_guard_service`
  - 未来负责 generic response legality 与稳定 HTTP 分类
- `anti_bot_detector`
  - 未来负责 challenge / gateway / suspicious HTML 分类
  - 当前不做 bypass

### 6.3 推荐数据流

未来 3-B 如果进入实现，推荐数据流应为：

1. `source_engine`
2. `request_profile_service`
3. `request_runtime_coordinator`
4. `request_body_encoder`
5. `fetch_service`
6. `response_guard_service`
7. `anti_bot_detector`
8. `parser_engine`
9. `content_parse_service`

原因：

- 请求描述问题与响应识别问题需要独立于 transport 和 parsing
- 这样可以在不重写现有主链的前提下增加复杂度
- 也能把“识别”与“绕过”拆开，避免提前越界

## 7. 当前最安全的 3-B 停留点

当前项目最安全的 3-B 停留点是：

- `L2` 完成设计
- `L3` 只完成检测与分类设计
- `L4/L5` 明确延后
- 仓库只落文档、Traceability、错误码、测试规划

### 7.1 3-B.1 固定结论摘要

#### `request body mode`

- 当前项目已隐式支持：
  - `query`
  - `form`
- 应定义显式 enum：
  - `query`
  - `form`
  - `json`
  - `raw`
- 首批真正允许进入实现的 mode 只建议开放：
  - `query`
  - `form`
- mode 应挂在内部 `request descriptor`，而不是 router / importer / public source schema

#### `header template / signature placeholder`

- header template 属于请求描述层
- 应与 body mode 一起挂在内部 `request descriptor`
- signature placeholder 当前只允许：
  - 建模
  - 能力标记
  - 错误分类
- 当前明确不允许真实求值
- 下一轮若做最小实现，模板 helper 先留在 `request_profile_service` 内部

#### `response_guard / anti_bot_detector`

- 推荐保留两层，而不是合并
- `response_guard` 负责：
  - timeout / 429 / content-type mismatch / generic legality checks
- `anti_bot_detector` 负责：
  - challenge
  - gateway
  - suspicious HTML
  - JS/browser-required 信号识别
- 两者当前都只允许：
  - 识别
  - 分类
  - 错误码映射
- 当前不允许：
  - 绕过
  - 自动恢复执行
  - 自动重试到成功

#### 第一批允许入代码的 3-B 错误码

推荐控制在 5 个以内，并优先选择纯 HTTP / 纯 preflight 可判定项：

- `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
- `LEGADO_INVALID_HEADER_TEMPLATE`
- `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
- `LEGADO_REQUEST_TIMEOUT`
- `LEGADO_RATE_LIMITED`

以下仍保留为文档预留，不进入首批代码：

- `LEGADO_REQUEST_PROFILE_INVALID`
- `LEGADO_REQUEST_RETRY_EXHAUSTED`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`

以下明确延后：

- `LEGADO_JS_EXECUTION_REQUIRED` -> `3-C`
- `LEGADO_BROWSER_STATE_REQUIRED` -> `3-D`

原因：

- 现有 skeleton 已经足够证明接缝位置
- 当前最大的风险不是“没有代码”，而是“过早把设计写成运行时实现”
- 再新增 hook/schema 代码，并不会比文档设计提供更多必要证据

## 8. 为什么当前不做 JS / Browser Fallback

### 8.1 不做 JS 的原因

- 当前项目还没有 response classification 层
- 直接引入 JS 会让问题从“请求运行时设计”跃迁为“脚本执行环境设计”
- 这属于 3-C，不应在 3-B 设计阶段提前实装

### 8.2 不做 Browser Fallback 的原因

- 当前项目仍没有 anti-bot / challenge 检测层的稳定分类
- 直接引入浏览器态会让项目从 HTTP 抓取升级为运行环境兼容
- 这属于 3-D，不应在 3-B 设计阶段提前实装

## 9. 风险点

- 如果把 retry / redirect / anti-bot 直接塞进 `fetch_service.py`，会污染 L0 传输层
- 如果把 response classification 混进 `content_parse_service.py`，会模糊“风险识别”和“内容解析”
- 如果把 request body mode 直接塞进现有 `OnlineRequestDefinition` 而不先设计 schema 演进，会破坏现有稳定契约
- 如果把识别能力表述成绕过能力，会造成阶段口径失真

## 10. 暂缓项

当前明确暂缓：

- retry / backoff 的生产级策略
- challenge 处理
- anti-bot 绕过
- JS 求值
- 动态签名生成
- browser fallback
- WebView
- Playwright / Selenium / Puppeteer / Chromium 接入
- Redis / MQ / 独立爬虫服务
- importer 接受高风险字段

## 11. 测试规划

即使本轮不落代码，未来 3-B 进入实现前也应先准备以下测试：

### 11.1 request profile 配置验证

- request profile 配置错误分类测试
- invalid header template 分类测试
- unsupported request body mode 分类测试
- unsupported signature placeholder 分类测试
- body mode 与 query/body/header 组合验证测试

### 11.2 风险响应识别

- generic timeout 分类测试
- `429` / rate limited 分类测试
- suspicious HTML 响应分类测试
- challenge detected 分类测试
- anti-bot gateway 分类测试
- retry exhausted 分类测试（仅在真正引入 retry 之后）

### 11.3 零破坏验证

- 旧 discovery / preview / online books 调用方式不需要新增参数
- 旧 online source validate/create/update 不受影响
- Phase 2 importer -> detail -> catalog -> chapter 回归继续通过
- 本地 TXT 链路不受影响

## 12. 本轮设计结论

本轮只做 Phase 3-B 设计已经足够推进项目。

当前 **没有证据** 表明必须新增代码骨架，才能回答 3-B 的架构问题。

因此当前最稳妥、最符合阶段约束的结论是：

- 本轮停留在设计层
- 不进入 3-B 实装
- 不新增代码
- 只更新文档、Traceability、错误码与测试规划
- 下一步最小任务已经收敛为：
  - 仅在内部 runtime descriptor / preflight 校验层起步
  - 先做 `body mode / header template / signature placeholder`
  - 不触碰 router / importer / DB / UI / 主流程语义

## 13. 3-B.2 已落地的最小 preflight 范围

当前仓库已经实际落地的 3-B.2 范围仅包括：

- 内部 `RequestBodyMode` enum
- 内部 `RequestRuntimeDescriptor`
- 内部 `HeaderTemplateSpec`
- 内部 `SignaturePlaceholderSpec`
- `request_profile_service` 中的单点 preflight hook
- 3 个错误码的最小分类：
  - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
  - `LEGADO_INVALID_HEADER_TEMPLATE`
  - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`

### 13.1 当前已落地什么

- `query / form / json / raw` 已在内部 enum 建模
- `query / form` 已进入 preflight 允许范围
- `json / raw` 当前仍只属于“已建模但未执行”，会在 preflight 被拒绝
- header template 已能做静态可接受性校验：
  - 空值不会崩溃
  - 明显动态/执行型模板会被拒绝
  - signature-like header/template 会被分类为 unsupported signature flow
- signature placeholder 已能做占位识别与拒绝分类
- 无 descriptor 时旧请求链路保持不变

### 13.2 当前未落地什么

- header template 求值
- header template 注入执行
- signature engine
- json/raw body 真正编码与发送
- response_guard
- anti_bot_detector

### 13.3 当前仍然不支持什么

- 自动签名生成
- JS 执行
- 浏览器态 / WebView
- suspicious HTML / challenge / gateway 检测
- retry / backoff / rate limit 执行策略

### 13.4 当前最小代码落点

本轮最小代码落点已经证实为：

- schema/descriptor 放在 `backend/app/schemas/online_runtime.py`
- preflight hook 放在 `backend/app/services/online/request_profile_service.py`

这样做的原因是：

- 不改 router
- 不改 importer
- 不改 DB
- 不改前端
- 不改 `fetch_service` 的传输职责

## 14. 3-B.3 已落地的最小 generic response_guard 范围

当前仓库已经额外落地的 3-B.3 范围仅包括：

- `response_guard_service` 的最小 helper
- `fetch_service` 中的单点 post-response / transport exception 分类接入
- 2 个 generic response 错误码：
  - `LEGADO_REQUEST_TIMEOUT`
  - `LEGADO_RATE_LIMITED`

### 14.1 当前已落地什么

- transport timeout 现在会被稳定映射为：
  - `LEGADO_REQUEST_TIMEOUT`
- HTTP 429 现在会被稳定映射为：
  - `LEGADO_RATE_LIMITED`
- 正常 2xx 响应不会触发本轮新增分类
- 非 429 的其他 HTTP 错误仍保持原 generic error 路径

### 14.2 当前没有落地什么

- retry / backoff / rate limit 执行策略
- suspicious HTML 检测
- challenge 检测
- gateway / WAF 检测
- browser required / js required 检测
- anti-bot detector

### 14.3 为什么这仍然只是 generic response classification

本轮分类只依赖：

- `httpx.TimeoutException`
- `response.status_code == 429`

本轮没有依赖：

- 响应 HTML 内容语义
- 站点指纹
- 反爬页面特征
- challenge 页面结构

因此这仍然只是 generic response_guard 的最小分类，不属于 detector。

## 15. 3-B.4 决策轮结论

本轮只处理一个问题：

> 在 timeout / HTTP 429 之外，response_guard 是否还应该继续吸收新的 generic classification？

### 15.1 `empty response` 的当前结论

当前结论：**暂不纳入 generic response_guard**

原因：

- 在当前项目里，“空响应”很容易与 stage 语义混在一起：
  - search 可能是“无结果”
  - detail/catalog/content 可能是 parser required-field 问题
  - content 为空也可能是站点内容本身为空、缺章、占位页、或正文抽取失败
- 仅凭“body 为空”并不能稳定回答：
  - 这是 transport/generic 问题
  - 还是 parser/input semantics 问题
- 误伤风险偏高
- 当前没有足够仓库证据支持稳定单测矩阵

因此它更适合作为：

- parser / content_parse / site semantics 问题

而不是当前 response_guard 的下一步实现目标。

### 15.2 `content-type mismatch / unacceptable response metadata` 的当前结论

当前结论：**只保留极窄候选，不进入下一轮默认实装**

原因：

- 它比 empty response 更接近 generic HTTP metadata 问题
- 但在现有项目中仍然存在明显耦合风险：
  - expected response type 来自 stage definition
  - 某些站点会返回非标准 content-type
  - HTML 预期路径比 JSON 预期路径更容易误判
- 当前 `fetch_service` 已经有通用文本错误：
  - `Response type mismatch: expected ...`
- 若现在直接把它升级成稳定错误码，很容易把 parser/stage 语义问题过早写死

因此当前只接受以下文档层判断：

- 若未来真的继续扩 response_guard，content-type mismatch 只能在**极窄条件**下再讨论：
  - 明确期望 `json`
  - 响应明确声明非 JSON content-type
  - 且不会与 detector/站点语义混淆

本轮不进入实现。

### 15.3 `response_guard` 与 `anti_bot_detector` 的边界补钉

本轮进一步固定边界：

- `response_guard` 只负责：
  - transport exception
  - HTTP status 层稳定分类
  - 极少量、明确可复现的 response metadata 问题
- 一旦分类需要依赖以下任一内容，就已经不属于 response_guard：
  - response body 文本语义
  - HTML 内容扫描
  - DOM/结构分析
  - suspicious page phrase / challenge wording
  - gateway/WAF 特征
  - browser/js-required 推断

换句话说：

- 看 status / exception / 明确 metadata -> 仍可能是 response_guard
- 看 body meaning / page semantics / site fingerprints -> 已经是 detector

### 15.4 下一轮最小任务建议

当前推荐下一轮不是继续扩 response_guard，而是：

- 进入 **detector 设计轮**

原因：

- response_guard 的 generic 空间目前已基本收紧到：
  - timeout
  - HTTP 429
- empty response 证据不足
- content-type mismatch 只有很窄的候选空间，还不足以值得优先实现
- 若继续硬扩 response_guard，更容易踩进 detector 边界

因此当前最合理的下一步是：

- **不再继续扩 response_guard 实装**
- 先做 detector 边界设计轮

## 16. 3-B.5 detector / anti-bot 边界设计轮结论

### 16.1 当前仓库基线

当前仓库已经能稳定证明：

- `response_guard_service.py` 当前只分类：
  - `httpx.TimeoutException`
  - HTTP `429`
- `fetch_service.py` 当前仍只负责：
  - transport 执行
  - response size limit
  - response type mismatch 校验
  - generic response guard hook
- `source_engine.py` 当前已经天然位于：
  - `fetch_stage_response(...)`
  - `parse_*_preview(...)`
  之间
- 当前仍然 **没有** detector service
- 当前仍然 **没有** suspicious HTML / challenge / gateway / browser-required / js-required 的响应后分类代码

因此，当前仓库已经足够支撑 detector 边界设计，但还不足以直接进入 detector 实装。

### 16.2 detector 的问题范围

detector 只应用于以下这类响应后问题：

- 分类已经不能只看 status / exception / metadata
- 必须读取 response body meaning
- 必须读取 HTML semantics
- 必须识别 challenge wording / challenge markers
- 必须识别 gateway / WAF interception fingerprints
- 必须识别 browser-required / js-required 的 body-level hints

detector 当前 **不** 应负责：

- transport timeout
- HTTP 429
- generic `4xx/5xx`
- 纯 metadata 问题
- 仍然高度依赖 parser/stage/site semantics 的 empty response 争议

当前 detector 的允许职责固定为：

- classification only
- signal labeling only
- stable error mapping only
- stop-execution only

当前 detector 的明确非职责仍然是：

- anti-bot bypass
- 自动 retry / backoff / fallback
- cookie refresh orchestration
- JS 执行
- browser / WebView 执行

### 16.3 `response_guard` 与 detector 的代码边界

基于当前代码链路，未来顺序应固定为：

1. `preflight`
2. `fetch`
3. `response_guard`
4. `detector`
5. `parser / content_parse`

这样划分的原因是：

- `response_guard` 必须留在 `fetch_service.py` 附近，因为它需要看到 transport exception 与稳定 HTTP 信号
- detector 不应继续塞进 `fetch_service.py`，否则传输层会开始承担 body semantics 逻辑
- detector 应在 `fetch_stage_response(...)` 返回 `RawFetchResponse` 之后接入
- detector 应在 `parse_*_preview(...)` 消费正文语义之前接入
- 因此 detector 的未来最小接缝更适合放在：
  - `source_engine.py`
  - 或一个非常薄的 future coordinator

未来 detector 的输入契约应优先固定为：

- `RawFetchResponse`
- 小范围 stage context
  - 如 stage name / expected response type / requested URL

未来 detector 的长期输入契约 **不** 应直接绑定为：

- 原始 `httpx.Response`
- router payload
- importer schema

未来 detector 的输出契约应是：

- structured classification result
- 或由该结果映射出的稳定 runtime error

未来 detector 的输出契约 **不** 应包含：

- retry instruction
- bypass instruction
- browser execution plan
- recovery strategy

### 16.4 第一批 detector 候选能力

本轮固定的 detector 候选集合为：

- suspicious HTML candidate
- anti-bot challenge candidate
- gateway / WAF interception candidate
- browser-required candidate signal
- js-required candidate signal

但它们当前的状态并不相同：

- suspicious HTML
  - `documented_only`
  - 不是下一轮默认实装目标
  - 原因：heuristic 空间太宽，最容易与正常 HTML 或 parser 失败混淆
- anti-bot challenge
  - future `candidate_for_first_implementation`
  - 仅限 classification
  - 不等于 challenge solving
- gateway / WAF interception
  - future `candidate_for_first_implementation`
  - 仅限 classification
  - 不等于 bypass
- browser-required
  - 当前只在 detector 边界层建模
  - runtime support 仍然 `deferred to 3-D`
- js-required
  - 当前只在 detector 边界层建模
  - runtime support 仍然 `deferred to 3-C`

### 16.5 为什么 suspicious HTML 继续更保守

与 challenge / gateway 相比，suspicious HTML 仍然最容易把 generic heuristic、parser semantics 与 site-specific semantics 混在一起。

当前仓库还不足以稳定定义：

- 一个低误伤的 suspicious HTML 规则集
- 一个不混入站点私货的测试矩阵
- 一个稳定区分以下情况的最小边界：
  - 正常 HTML 内容页
  - parser 输入异常
  - anti-bot challenge page
  - generic unexpected HTML

所以 3-B.5 的最保守结论仍是：

- 继续保留 suspicious HTML 文档建模
- 但不把它升级成下一轮默认实装目标

### 16.6 为什么 browser-required / js-required 仍然继续 deferred

即便未来 detector 可以识别出 body-level browser/js-required signals，也不代表仓库已经准备好把这些分类升级成“可支持的运行时能力”。

当前仓库仍然缺少：

- JS sandbox execution
- browser / WebView fallback
- 相关路径的资源隔离与恢复策略

因此 3-B.5 保持执行侧状态不变：

- `LEGADO_JS_EXECUTION_REQUIRED` -> `deferred to 3-C`
- `LEGADO_BROWSER_STATE_REQUIRED` -> `deferred to 3-D`

这样可以避免把“信号可建模”误写成“能力已支持”。

### 16.7 Step 1 / Step 2 判断

#### Step 1：本轮只做文档与决策是否已经足够

结论：**足够**

原因：

- 当前仓库已经有足够证据固定 detector 的问题范围
- 当前仓库已经有足够证据固定 `response_guard` / detector 的调用顺序与接缝
- 当前仓库已经有足够证据固定 detector 候选能力与错误码状态分层
- 当前仓库已经有足够证据把下一轮收敛到更小的 detector skeleton 决策任务

#### Step 2：当前是否存在“必须落代码”的充分证明

结论：**不存在**

当前还没有证据能证明：

- 只做文档会阻塞下一轮
- detector skeleton 已经小到可以安全直接落代码
- 在 detector 输入/输出契约还未固定前，加代码空壳会比边界决策本身更有价值

因此 3-B.5 默认停在文档层。

### 16.8 下一轮最小任务

当前最小、最稳妥的下一步应是：

- **Phase 3-B.6：detector 最小静态分类骨架决策轮**

而不是：

- 直接进入 detector 实装
- 直接实现 suspicious HTML
- 直接实现 challenge / gateway
- 直接实现 browser-required / js-required

3-B.6 只应继续固定：

- detector 输入契约
- detector 输出契约
- first-batch sample matrix
- challenge / gateway 候选 heuristic 的最小边界

当前阶段口径必须保持为：

> Phase 3-B.5 仅完成 detector / anti-bot 边界设计，仓库尚未进入 detector 实装，尚未进入 anti-bot bypass，尚未进入 3-C / 3-D。

## 17. 3-B.6 detector 最小静态分类骨架决策轮结论

### 17.1 当前 detector 仍然缺什么

基于当前仓库，detector 仍然缺少四个最小骨架定义：

- 稳定输入契约
- 稳定输出契约
- first-batch sample matrix
- challenge / gateway 的最小 generic heuristic 边界

并且当前仓库还有一个直接影响 detector 设计的现实限制：

- `fetch_service.py` 在 `response.status_code >= 400` 时会直接抛错
- 这意味着 future detector 不能简单被设计成“只消费成功返回的 `RawFetchResponse`”
- 如果未来 detector 要覆盖 `403/503` 这类 challenge / gateway HTML block pages，就必须先有一个不直接绑定 `httpx.Response`、也不只依赖成功路径 `RawFetchResponse` 的中间输入契约

因此，本轮比 heuristic 代码更优先的工作，是把静态骨架先在设计层定死。

### 17.2 detector 输入契约推荐

当前不推荐把 detector 直接绑定为：

- 完整 `httpx.Response`
- 或 parser 层已经语义化后的高层对象

本轮推荐 future detector 输入契约采用：

- **normalized detection input**

它应由两层组成：

1. `request/stage context`
2. `response evidence summary`

推荐的最小字段集合为：

- `stage`
  - `search | detail | catalog | content`
- `expected_response_type`
  - `html | json`
- `requested_url`
- `final_url`
- `status_code`
- `content_type`
- `redirected`
  - 基于 `requested_url != final_url`
- `body_text_preview`
  - 只保留受约束的文本摘要
  - 推荐上限：`4096` 字符
- `body_text_length`

本轮不推荐在 first skeleton 中把以下内容作为必需输入：

- 完整 header bag
- 原始二进制 body
- 完整 HTML DOM
- parser 输出结果
- 任意站点特有上下文

原因：

- 完整 `httpx.Response` 会把 detector 与 transport 实现绑死
- 完整 body / DOM 会让 detector 更容易长成“大杂烩分析器”
- parser 输出会把 detector 与语义解析层混在一起
- 受约束的 `body_text_preview` 更适合 future heuristic 测试、回放、裁剪与样本治理

关于 header：

- 当前 first skeleton 只把 `content_type` 视为稳定输入
- 未来若确有必要，再讨论一个极小 allowlist 的 `header_hints`
- 但不应在本轮默认要求“保留完整 headers”

### 17.3 detector 输出契约推荐

当前不推荐 detector 直接输出：

- 单一错误码
- 或裸 `signal list`

本轮推荐 future detector 输出契约采用：

- **structured classification result**

再由上层将其映射到稳定错误码。

推荐的最小输出字段集合为：

- `category`
  - `challenge_candidate`
  - `gateway_candidate`
  - `suspicious_html_candidate`
  - `browser_required_candidate`
  - `js_required_candidate`
  - `no_match`
- `matched_signals`
  - 稳定 signal id 列表
- `evidence_snippets`
  - 短文本证据片段
  - 仅用于测试与 traceability
- `recommended_error_code`
  - 可为空
- `status`
  - `candidate`
  - `documented_only`
  - `deferred_to_3c`
  - `deferred_to_3d`
- `deferred_requirement_hint`
  - 仅用于文档建模
  - 例如：
    - `js_runtime`
    - `browser_runtime`
    - `manual_review`
    - `none`

本轮不推荐在 first skeleton 中放入：

- `retry plan`
- `fallback plan`
- `auto recovery action`
- 数值型 `confidence`

原因：

- 直接错误码输出会丢失 traceability
- 裸 signal list 会把错误码映射责任散落到多个上层
- 恢复/绕过类字段极易被误解成“已支持自动处理”
- `confidence` 在 first skeleton 阶段最难保证可测、可复现、可稳定

### 17.4 first-batch sample matrix 推荐范围

本轮推荐 first-batch sample matrix 的正向候选范围只覆盖：

- challenge candidate
- gateway / WAF interception candidate

本轮不建议进入 first-batch 默认样本的项目：

- suspicious HTML
- browser-required
- js-required

原因分别是：

- `suspicious HTML`
  - 仍然最容易与 parser/stage/site semantics 混淆
- `browser-required` / `js-required`
  - 当前更适合作为 detector 输出中的 deferred capability hint
  - 而不是 first-batch detector 样本目标

但 first-batch matrix **仍然必须**包含负样本/对照样本，用于防止 challenge / gateway 误判。

推荐样本字段最小集合：

- `sample_id`
- `stage`
- `response_status`
- `content_type`
- `requested_url`
- `final_url`
- `body_snippet`
- `expected_category`
- `expected_error_code`
- `expected_error_code_status`
- `expected_matched_signals`
- `notes`

关于 stage：

- stage 字段应成为所有样本的必填字段
- 但 first-batch 不要求四个 stage 的正样本全覆盖
- 更合理的最小做法是：
  - challenge/gateway 正样本若干
  - 外加跨 stage 的负样本/相似页样本

推荐的 first-batch 样本组成是：

- challenge positive samples
- gateway positive samples
- normal login page negative samples
- normal error page negative samples
- normal “no results”/空列表 negative samples

这样才能避免 detector 一开始就只学会“关键词命中”而没有误判约束。

### 17.5 challenge / gateway 的最小 generic heuristic 边界

本轮固定第一轮 heuristic 只允许使用：

- **极少数 generic signal bundles**

而不是任意扩大到更多 pattern，更不是 site-specific 线索。

#### challenge candidate 的最小 generic signals

推荐只保留以下几类 signal bundle：

- 标题/正文中的 human-verification 类短语组合
  - 例如：
    - `verify you are human`
    - `human verification`
    - `security check`
    - `checking your browser`
    - `enable javascript and cookies to continue`
- 带有验证语义的交互控制组合
  - challenge wording + form/button/checkbox/captcha 控件痕迹
- 泛化的 path / final-url hint
  - 例如包含：
    - `/challenge`
    - `/captcha`
    - `/verify`
  - 但它们只能作为辅助信号，不能单独成立

#### gateway candidate 的最小 generic signals

推荐只保留以下几类 signal bundle：

- deny / intercept wording 组合
  - 例如：
    - `access denied`
    - `request blocked`
    - `blocked by security rules`
    - `forbidden by security policy`
- firewall / security-service wording 组合
  - 例如：
    - `security service`
    - `firewall`
    - `web application firewall`
    - `protected by security rules`
- 支撑性状态码组合
  - `403`
  - `503`
  - 仅能作为辅助信号，不可单独成立
- 支撑性 final-url/path hints
  - 例如：
    - `/blocked`
    - `/denied`
    - `/challenge`

#### 第一轮明确不应纳入 generic 边界的内容

- vendor brand names 作为核心规则
  - 例如：
    - `cloudflare`
    - `akamai`
    - `imperva`
    - `incapsula`
- 某个站点专有的表单结构
- 某个站点专有的按钮文案
- 单个关键词单独命中即判定 challenge/gateway

#### 明确高误伤风险的模式

以下模式虽然常见，但第一轮不应单独作为 detector 命中依据：

- 单独出现 `verify`
- 单独出现 `security`
- 单独出现 `continue`
- 普通登录页里的 captcha 控件
- 普通 403/404/维护页
- 普通“请登录后继续”页面

结论：

- 第一轮 heuristic 必须以**组合信号**为主
- 不允许以**单词命中**或**站点私货**为主

### 17.6 为什么本轮默认仍不进 detector 代码层

#### Step 1：本轮只做文档、样本矩阵与决策是否已经足够

结论：**足够**

原因：

- 当前最缺的是 detector skeleton contract，而不是 detector code shell
- first-batch 样本范围与 heuristic 边界如果不先钉死，下一轮代码很难写得小而稳
- 当前 `fetch_service.py` 的 `status_code >= 400` 早抛错行为，本身就说明“先定输入契约”比“先写 detector 代码”更重要

#### Step 2：当前是否有充分证据证明必须落代码

结论：**没有**

当前没有充分证据表明：

- 不落代码会阻塞下一轮
- detector 空壳已经小到不可再小
- 在输入/输出/sample matrix 尚未固定前，加代码不会造成阶段误导

因此 3-B.6 默认停在文档层。

### 17.7 下一步最小可执行任务

本轮之后，最小、最稳妥的下一步建议是：

- **Phase 3-B.7：detector 最小静态分类骨架实现（纯内部 schema/result/sample-fixture 层）**

它应严格限制为：

- 内部 detector input schema
- 内部 detector output schema
- challenge/gateway first-batch sample fixtures
- 纯离线、纯静态、纯可单测的分类骨架

它仍然不应包括：

- live runtime hook
- suspicious HTML heuristic
- browser/js-required heuristic
- anti-bot bypass
- JS / browser fallback

当前阶段口径必须保持为：

> Phase 3-B.6 仅完成 detector 最小静态分类骨架决策，仓库尚未进入 detector / anti-bot 实装，尚未进入 3-C / 3-D。

## 18. 3-B.7 已落地的 detector 最小静态分类骨架

### 18.1 当前已落地什么

当前仓库已经以纯内部、纯离线、纯可单测的方式落地了：

- 内部 detector input schema
- 内部 detector output schema / classification result
- first-batch sample fixtures
- 纯静态 classification skeleton
- 对应单元测试

当前实际代码落点为：

- `backend/app/schemas/online_detector.py`
- `backend/app/services/online/detector_skeleton.py`
- `backend/tests/fixtures/online_detector_samples.json`
- `backend/tests/test_online_detector_skeleton.py`

当前 input schema 已承载：

- `stage`
- `expected_response_type`
- `requested_url`
- `final_url`
- `status_code`
- `content_type`
- `redirected`
- `body_text_preview`
- `body_text_length`

当前 output schema 已承载：

- `category`
- `status`
- `matched_signals`
- `evidence_snippets`
- `recommended_error_code`
- `deferred_requirement_hint`

当前 first-batch fixtures 已覆盖：

- challenge candidate 正样本
- gateway candidate 正样本
- login / maintenance / no-results 等负样本

当前 classification skeleton 当前只产出：

- `challenge_candidate`
- `gateway_candidate`
- `no_match`

### 18.2 当前没有落地什么

当前仍然 **没有** 落地：

- live detector hook
- `fetch_service.py` 中的 detector 接入
- `source_engine.py` 中的 detector 接入
- suspicious HTML detection
- browser-required detection
- js-required detection
- anti-bot bypass
- retry / backoff / rate limit 执行策略

### 18.3 当前仍然不支持什么

当前必须继续明确表述为 **不支持**：

- detector live runtime
- challenge / gateway 的线上执行检测
- suspicious HTML detector
- browser/js-required detector
- JS / WebView / browser fallback
- anti-bot recovery / bypass

### 18.4 为什么这仍然不等于 detector runtime

因为本轮骨架只运行在：

- 内部 schema
- 离线 sample fixtures
- 单元测试

它当前 **不**：

- 消费 live fetch path
- 消费 live `source_engine` path
- 改变任一 public API
- 改变任一 importer / DB / frontend 行为
- 触发线上错误映射

因此本轮正确口径必须是：

> detector skeleton-modeled offline, not implemented in runtime

### 18.5 当前 error code 的正确理解

当前骨架允许在 classification result 中推荐：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

但这只表示：

- detector static skeleton 已建模这些推荐错误码

并不表示：

- live runtime 已经会抛出这些错误码
- challenge/gateway detection 已上线

### 18.6 下一步最小任务

在 3-B.7 之后，最小的下一步建议应是：

- **Phase 3-B.8：detector live 接缝决策轮**

该轮应先回答：

- `fetch_service.py` 的 4xx/5xx 早抛错如何与 detector 输入契约衔接
- detector live hook 到底放在 `source_engine.py` 还是 future coordinator
- challenge/gateway 候选错误码何时才允许从 skeleton-modeled 升到 runtime-implemented

在这一步之前，仍不应直接进入：

- suspicious HTML runtime
- browser/js-required runtime
- anti-bot bypass

## 19. 3-B.8 detector live 接缝决策轮结论

### 19.1 当前仓库证据与缺口

当前仓库已经足以证明以下事实：

- `fetch_service.py`
  - 当前只负责 transport 执行、response size limit、generic response_guard、response type mismatch 与 `status_code >= 400` 的早抛错
- `response_guard_service.py`
  - 当前只负责：
    - timeout
    - HTTP 429
  - 不应继续长成 detector
- `source_engine.py`
  - 当前天然位于：
    - `fetch_stage_response(...)`
    - `parse_*_preview(...)`
    之间
  - 同时拥有最稳定的 stage context
- `parser_engine.py` / `content_parse_service.py`
  - 当前已经开始消费 `RawFetchResponse.text/json_data`
  - 一旦 detector 放到这里，就已经混入 parser/body semantics
- `detector_skeleton.py`
  - 当前只消费内部 `DetectorInput`
  - 当前只在离线 fixtures / tests 中工作

当前真正缺的不是 detector heuristic 本身，而是：

- future live detector 的最小输入来源
- future live detector 的单点 hook 接缝
- `fetch_service.py` 早抛错与 detector 读取 challenge/gateway block page 的兼容策略
- detector 错误码从 `skeleton-modeled` 升到 `runtime-implemented` 的统一门槛

因此本轮正确动作仍然是：

- 先固定 live seam
- 暂不进入 live detector runtime 代码

### 19.2 决策 1：live 输入来源与裁剪边界

#### 方案 A：直接在 `fetch_service.py` 里构造 `DetectorInput`

优点：

- 最靠近 transport response / exception
- 最容易看到原始状态码与 headers

缺点：

- 会把 detector 输入构造直接塞进 transport 层
- `fetch_service.py` 当前并不稳定拥有 stage context
- 容易让 transport 层开始理解 body semantics
- 若未来还有别的 detector 输入来源，会在多个层重复构造

风险：

- 污染 `fetch_service.py`
- 把 detector 与 transport 实现绑死
- 增大后续回退成本

#### 方案 B：由 `source_engine.py` 在 stage 级直接构造 `DetectorInput`

优点：

- 最稳定地拥有 stage context
- 已经天然位于 fetch 与 parser 之间
- 不需要把 detector 输入构造塞进 parser

缺点：

- 如果所有 detector 细节都直接堆进 `source_engine.py`，会让它变成大杂烩
- 仍然需要一个中间层去统一 success/error outcome

风险：

- 若没有进一步抽薄，会让 `source_engine.py` 同时承担：
  - stage orchestration
  - detector input adaptation
  - detector dispatch
  - error mapping

#### 方案 C：通过 future adapter/coordinator 在 `fetch` 与 `parser` 之间构造 `DetectorInput`

优点：

- 能保持 detector 继续只吃 normalized `DetectorInput`
- 能把 response / exception summary 的裁剪集中到单点
- 能由 `source_engine.py` 提供 stage context，同时不把 `source_engine.py` 本体写胖
- 最利于未来独立回退

缺点：

- 需要额外定义一个薄的 live seam adapter/coordinator 契约
- 当前仓库还没有这个中间层

风险：

- 若 adapter 设计过重，会提前长成 runtime coordinator
- 若 adapter 设计过宽，会变成新的 transport envelope 大杂烩

#### 推荐结论

推荐 **方案 C**，并固定以下边界：

- future live detector 仍应坚持使用 normalized `DetectorInput`
- `DetectorInput` 不应由 detector 自己从原始对象中抽取
- `DetectorInput` 应由 future adapter/coordinator 在单点构造
- `source_engine.py` 提供 stage context
- `fetch_service.py` 只继续提供 transport outcome

不推荐方案 A 的原因：

- 会过度污染 transport 层
- 会让 `fetch_service.py` 提前承担 detector 职责

不推荐方案 B 的原因：

- 高层方向是对的，但如果没有一个明确的薄 adapter，`source_engine.py` 容易继续膨胀

### 19.3 决策 2：live hook 最合适放在哪一层

#### 方案 A：hook 放在 `fetch_service.py`

优点：

- 最早看到 response / exception
- 理论上最容易统一 success / error outcome

缺点：

- 直接污染 transport 叶子层
- 缺少稳定 stage context
- 会把 body-level detector 逻辑塞到不该理解页面语义的层

风险：

- `fetch_service.py` 变成 transport + detector 混合层

#### 方案 B：hook 放在 `source_engine.py`

优点：

- 当前最自然的编排接缝
- 已经位于 fetch 与 parser 之间
- stage context 最完整

缺点：

- 如果直接把 detector dispatch、input adaptation、error mapping 都写进去，`source_engine.py` 会继续变厚

风险：

- `source_engine.py` 可能演变成新的运行时大杂烩

#### 方案 C：hook 放在 future coordinator / adapter，并由 `source_engine.py` 调用

优点：

- 逻辑位置仍然处于 `source_engine.py` seam
- 实现责任却可以保持为一个薄中间层
- 既保留 stage context，又不污染 parser / fetch
- 最利于后续独立回退

缺点：

- 当前仓库还没有这个中间层
- 需要下一轮进一步把这个最小 adapter 结构钉死

风险：

- 若 coordinator 过重，会提前承担过多 runtime orchestration 责任

#### 推荐结论

推荐 **方案 C**，并把结论写清为：

- future live hook 的逻辑接缝位于：
  - `source_engine.py`
  - `fetch_stage_response(...)` 之后
  - `parse_*_preview(...)` 之前
- 但实际 detector dispatch 不建议直接硬塞进 `source_engine.py`
- 更推荐由 `source_engine.py` 调用一个 future thin coordinator / adapter

不推荐方案 A 的原因：

- `fetch_service.py` 必须继续停留在 transport/generic response 层

不推荐方案 B 的原因：

- 直接把 live hook 细节堆进 `source_engine.py` 会放大后续维护成本

### 19.4 决策 3：`fetch_service.py` 早抛错与 detector 的兼容策略

#### 当前仓库真实结论

当前 `fetch_service.py` 的：

- `status_code >= 400` 早抛错

**会阻断** future detector 对一部分 challenge/gateway 候选响应的读取。

证据来自当前代码路径：

- `httpx.request(...)` 返回后
- `classify_generic_response_issue(...)` 只处理 429
- 若 `response.status_code >= 400`
  - 直接抛出 `FetchServiceError`
  - 不返回 `RawFetchResponse`
- 因此像 `403/503` 这类 gateway / challenge candidate 页面，当前 live path 无法把 body 继续交给 detector

受影响的 future use cases 至少包括：

- `403` challenge HTML
- `403` gateway / access denied block page
- `503` security service / WAF intercepted page

#### 方案 A：保持 `fetch_service.py` 现状，不为 detector 改动

优点：

- 对现有系统零侵入
- 最保守

缺点：

- future detector 无法覆盖关键的 `403/503` 候选场景
- challenge/gateway live 检测价值会明显受限

风险：

- 可能导致“看似有 live seam，实际无法看到关键样本”

#### 方案 B：future 引入 exception-to-summary adapter

优点：

- 可以继续保持 `fetch_service.py` 的公共行为不变
- 能把 fetch 的 success / early error outcome 统一裁剪成 detector 可读的 summary
- 是下一轮最小 live seam 讨论里最小、最保守的方向

缺点：

- 需要先定义：
  - 哪些错误需要保留 body snapshot
  - 哪些只保留 generic error
- 当前还没有这个 adapter 契约

风险：

- 若 summary 设计不当，仍可能丢失关键证据

#### 方案 C：future 引入 transport result envelope

优点：

- 理论上最完整
- 最适合长期扩展

缺点：

- 对现有 fetch 链路侵入最大
- 很容易演变成本轮不该开始的大重构

风险：

- 会让下一轮从“最小 live seam”升级成 transport contract 重写

#### 推荐结论

推荐 **方案 B** 作为下一轮最小入口方向：

- 当前不修改 `fetch_service.py` live 行为
- 当前只固定 future 方向为：
  - 引入 exception-to-summary style 的 live seam adapter 设计
- 暂不进入 transport result envelope 实装

不推荐方案 A 的原因：

- 它不足以支撑 future challenge/gateway live classification

不推荐方案 C 的原因：

- 对当前阶段过重
- 还不符合“最小不可再小”的下一轮入口要求

### 19.5 决策 4：错误码从 `skeleton-modeled` 升级到 `runtime-implemented` 的条件

#### 方案 A：只要 skeleton 能推荐错误码就升级

优点：

- 状态推进最快

缺点：

- 会把离线推荐错误码误写成 live runtime 已支持
- 阶段误导风险最高

风险：

- 误导为 anti-bot / challenge / gateway 已上线

#### 方案 B：必须 live seam 已接通且可稳定触发才升级

优点：

- 与当前仓库证据最一致
- 兼顾 Traceability 和阶段口径
- 能明确区分：
  - offline skeleton
  - runtime-implemented

缺点：

- 状态推进更保守

风险：

- 需要后续测试矩阵更完整

#### 方案 C：等完整 detector runtime 全部做完再升级

优点：

- 最保守

缺点：

- 过于迟滞
- 不利于分阶段、分能力推进

风险：

- 会让 challenge / gateway 明明已经具备最小 live classification，也长期无法反映在状态层

#### 推荐结论

推荐 **方案 B**，并固定 challenge / gateway 共用同一套升级门槛：

只有同时满足以下条件，才允许从 `skeleton-modeled` 升到 `runtime-implemented`：

1. live seam 已存在且仍是内部接缝
2. detector 在 live path 中能稳定收到 normalized `DetectorInput`
3. 对应错误码可被稳定触发，而不是只存在 `recommended_error_code`
4. 有正样本与负样本
5. 有单测与至少一层集成/回归验证
6. 文档、Traceability、错误码状态都继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

不推荐方案 A 的原因：

- 它会把“recommended error code”误写成“runtime 已会抛出”

不推荐方案 C 的原因：

- 不利于按最小 live classification 能力逐步升级

### 19.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续停在设计层，专门做更泛的 live seam 设计

优点：

- 最保守

缺点：

- 本轮已经把高层 seam 方向钉得比较清楚
- 再做泛设计，新增信息量有限

风险：

- 容易重复 3-B.8 的结论

#### 方案 B：进入最小 live seam skeleton 决策轮

优点：

- 仍然不进入 live runtime 实装
- 但能把下一轮继续收敛到最小可实装入口
- 能专门解决：
  - future exception-to-summary adapter 契约
  - detector live input summary 的最小字段集
  - `source_engine.py` 调用薄 coordinator 的边界

缺点：

- 仍然是决策轮，不是实现轮

风险：

- 需要严格限制范围，避免再度发散

#### 方案 C：直接进入 detector live hook 最小骨架实装

优点：

- 推进速度最快

缺点：

- 当前仍缺最小 live seam adapter 契约
- 当前仍缺对 early error outcome 的统一承载决策
- 直接实装最容易伤到 fetch/source/parser 边界

风险：

- 直接越界进入 detector live runtime

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小的任务集合应固定为：

- **Phase 3-B.9：detector live seam skeleton 决策轮**
- 只回答：
  - future exception-to-summary / fetch-outcome adapter 的最小 contract
  - `source_engine.py` 调用薄 coordinator 的最小边界
  - detector live input summary 的最小字段保留规则
  - 无 detector 命中时成功路径零破坏的最小测试矩阵

当前不推荐直接进入 live hook 实装，原因是：

- 仍缺最小 adapter 契约
- 仍缺 error outcome 到 detector input 的稳定收敛方式
- 仍缺最小 live seam success/error 双路径测试设计

当前更不应越级进入：

- browser/js runtime
- anti-bot bypass
- 3-C / 3-D

### 19.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**

原因：

- 当前仓库已经有足够证据固定 live 输入来源方向
- 当前仓库已经有足够证据固定 live hook 放置层次
- 当前仓库已经有足够证据确认 `fetch_service.py` 早抛错确实影响 future detector
- 当前仓库已经有足够证据固定错误码升级门槛

#### Step 2：如果主张本轮必须落代码，是否已经有充分证明

结论：**没有**

当前仍然无法证明：

- 不落代码会阻塞下一轮
- 需要落的代码已经小到不可再小
- 新增 live seam 代码不会构成 detector live runtime
- 新增代码不会影响既有 fetch/source/parser 链路

因此 3-B.8 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 live detector runtime 实装。
