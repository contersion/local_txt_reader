# Legado Phase 3-B Request Runtime Design

## 1. 文档定位

本文档只服务于 **Phase 3-B 强约束设计阶段**。

当前最新轮次进一步固定为：

- `Phase 3-B.26`：detector runtime-facing behavior activation minimal skeleton 实现
- 默认结论：只允许最小 internal runtime-facing behavior-activation contract/helper/carrying/tests/docs 落地
- 默认允许进入代码
- 默认不进入 runtime-facing behavior activation 生效

当前目标不是实现复杂请求运行时，而是：

- 扫描当前请求执行链
- 划清复杂请求问题边界
- 设计能力分层与模块接缝
- 设计错误码与测试规划
- 明确哪些能力必须后置，防止过早实装

当前默认结论：

> 本轮只允许最小 internal runtime-facing behavior activation skeleton 实装，不进入 runtime-facing behavior activation 生效。

当前轮次关键决策的完整方案比较，统一记录于：

- `docs/LEGADO_PHASE3B_DECISIONS.md`

在当前轮次之后，仓库已额外完成：

- `Phase 3-B.2`：最小 preflight 实装
- `Phase 3-B.3`：generic response_guard 最小分类实装
- `Phase 3-B.4`：response_guard 扩展前决策轮（文档/决策层）
- `Phase 3-B.5`：detector / anti-bot 边界设计轮（文档/决策层）
- `Phase 3-B.6`：detector 最小静态分类骨架决策轮（文档/决策层）
- `Phase 3-B.7`：detector 最小静态分类骨架实现（纯内部、纯离线）
- `Phase 3-B.8`：detector live 接缝决策轮（文档/决策层）
- `Phase 3-B.9`：detector live seam skeleton 决策轮（文档/决策层）
- `Phase 3-B.10`：detector live seam skeleton 最小内部结构实装（纯内部、纯非 live）
- `Phase 3-B.11`：detector live seam adapter 接入前决策轮（文档/决策层）
- `Phase 3-B.12`：detector live seam adapter 最小内部 skeleton 实装（纯内部、纯 no-op）
- `Phase 3-B.13`：detector live seam adapter 最小接入决策轮（文档/决策层）
- `Phase 3-B.14`：detector live seam adapter 最小 live-entry skeleton 实现（纯内部、纯 no-op）
- `Phase 3-B.15`：detector live behavior gating 决策轮（文档/决策层）
- `Phase 3-B.16`：detector live behavior minimal gating skeleton 实现（纯内部、纯 no-op）
- `Phase 3-B.17`：detector runtime-visible gating 决策轮（文档/决策层）
- `Phase 3-B.18`：detector runtime-visible minimal gating skeleton 实现（纯内部、纯 no-op）
- `Phase 3-B.19`：detector runtime error surface 决策轮（文档/决策层）
- `Phase 3-B.20`：detector runtime error surface minimal skeleton 实现（纯内部、纯 no-op）
- `Phase 3-B.21`：detector runtime-facing error gate 决策轮（文档/决策层）
- `Phase 3-B.22`：detector runtime-facing error gate minimal skeleton 实现（纯内部、纯 no-op）

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

## 20. 3-B.9 detector live seam skeleton 决策轮结论

### 20.1 当前 live seam 仍缺什么

在 3-B.8 之后，仓库已经知道：

- future detector 不应直接塞进 `fetch_service.py`
- future detector 接缝逻辑位于 `source_engine.py` 所在的 fetch -> parser seam
- future detector 需要能看见一部分当前会被 `fetch_service.py` 早抛错吞掉的 `403/503` 候选页信息

但当前仍然缺少真正能让下一轮 safely 起步的最小 contract：

- `exception-to-summary` 的最小 contract
- success / error 双路径 summary 的最小共享字段
- `source_engine -> thin coordinator/adapter` 的最小调用边界
- 不改 public 行为前提下的最小可接入点定义

因此本轮最重要的不是写 live seam 代码，而是先把 seam skeleton contract 定死。

### 20.2 决策 1：`exception-to-summary` 最小 contract

#### 方案 A：success / error 完全统一成一个 `DetectionInputSummary`

优点：

- 类型表面最简单
- 对 future detector 调用方看起来最统一

缺点：

- 当前 success path 与 error path 的可见性差异太大
- 很容易被迫伪造：
  - `final_url`
  - `status_code`
  - `content_type`
  - `body_text_preview`
- 一个大而全的 summary bag 很快会变得模糊

风险：

- 统一外形掩盖真实缺失数据
- 后续测试会出现“字段有但并不可信”的问题

#### 方案 B：success / error 各自独立 summary，但共享 base fields

优点：

- 最符合当前仓库真实信息边界
- 能避免伪造不存在的数据
- 可保留双路径差异，同时把共享 contract 压到最小
- 最利于 future adapter 再做 detector-ready normalization

缺点：

- 类型数会比单一 summary 多一层
- 下一轮需要明确 base / success / error 三者关系

风险：

- 若 base fields 设计过宽，仍可能演变成大 bag

#### 方案 C：先只做 error summary，success path 以后再并

优点：

- 最直接回应当前 `403/503` / exception 问题
- 初始范围最窄

缺点：

- success / error 双路径会在设计上失衡
- 下一轮仍然要补 success path，容易返工

风险：

- seam skeleton 从第一步就变成偏 error-only，后续不利于统一维护

#### 推荐结论

推荐 **方案 B**。

future `exception-to-summary` contract 应采用：

- `FetchOutcomeSummaryBase`
- `FetchSuccessSummary`
- `FetchErrorSummary`

其中最小共享字段推荐固定为：

- `stage`
- `expected_response_type`
- `requested_url`
- `fetch_outcome_kind`

error / success 各自可选补充：

- `final_url`
- `status_code`
- `content_type`
- `redirected`
- `body_text_preview`
- `body_text_length`
- `exception_kind`

不推荐方案 A 的原因：

- 当前仓库并不支持“单一 summary 且所有字段都有可信值”

不推荐方案 C 的原因：

- 3-B.9 的核心要求就是同时覆盖 dual-path，不应只做 error 半套

### 20.3 决策 2：success path / error path 的最小字段集合

#### 方案 A：字段尽量多，追求 future 一步到位

优点：

- 表面上 future 扩展余量最大

缺点：

- 与本轮“最小不可再小”原则冲突
- 很容易提前引入：
  - header bag
  - full body
  - parser hints
  - site-specific metadata

风险：

- 误复杂化风险最高

#### 方案 B：字段最小化，只保留当前确实必要字段

优点：

- 最符合 3-B.9 的目标
- 样本和测试最容易维护
- 最利于下一轮只做 summary/adapter schema 而不误入 live hook

缺点：

- 未来若新增 heuristic，需要后续小步补字段

风险：

- 需要明确哪些字段是 shared，哪些字段是 optional

#### 方案 C：按 stage 分裂不同字段集

优点：

- 理论上最贴合 stage 语义

缺点：

- 现在就按 stage 裂开，会让 seam skeleton 过早变复杂
- 不利于 summary fixture 与 contract 测试治理

风险：

- stage-specific 契约很容易提前膨胀成 parser-side contract

#### 推荐结论

推荐 **方案 B**。

当前最小共享字段建议固定为：

- `stage`
- `expected_response_type`
- `requested_url`
- `fetch_outcome_kind`

当前最小 optional 字段建议固定为：

- `final_url`
- `status_code`
- `content_type`
- `redirected`
- `body_text_preview`
- `body_text_length`
- `exception_kind`

当前必须禁止直接放入 summary 的内容：

- 完整 `httpx.Response`
- 完整 response headers
- 完整 body
- DOM / parser 结果
- 任意 site-specific hints

这样做的原因是：

- success / error 两条路径可以共享一组最小 contract
- 同时不强行伪造不存在的数据
- future adapter 仍有空间把 summary 转成 detector-ready normalization

### 20.4 决策 3：`source_engine -> thin coordinator/adapter` 的最小调用边界

#### 方案 A：在 `source_engine.py` 内部直接内嵌最小 adapter 逻辑

优点：

- 改动点最直观
- stage context 获取简单

缺点：

- 容易让 `source_engine.py` 继续变厚
- fetch / response_guard / detector summary / detector dispatch 都可能开始在同一文件堆积

风险：

- `source_engine.py` 会慢慢长成大 orchestrator

#### 方案 B：独立 thin adapter/coordinator，`source_engine.py` 只调用

优点：

- 最利于职责分离
- 最容易独立回退
- 能把下一轮继续限制在“summary/adapter schema”而不是 live hook

缺点：

- 需要多一个极薄的内部模块

风险：

- 如果边界没钉死，thin coordinator 也可能继续膨胀

#### 方案 C：在 `fetch_service.py` 内加 seam adapter

优点：

- 最靠近 transport outcome

缺点：

- 会让 transport 层开始承担 stage-aware seam adapter 责任
- 与 3-B.8 已固定边界冲突

风险：

- 污染 `fetch_service.py`

#### 推荐结论

推荐 **方案 B**。

future thin coordinator/adapter 的最小职责应只包括：

1. 调 fetch
2. 调 response_guard
3. 把 success / error outcome 裁剪成 summary
4. 在满足最小证据时再进入 detector-ready normalization
5. 决定结果是：
   - 继续进入 parser
   - 还是只在 future detector path 内部分类/上抛

它当前 **不应** 负责：

- retry / backoff / fallback
- anti-bot bypass
- parser semantics
- site-specific orchestration
- browser / JS runtime 决策

与 `source_engine.py` 的边界应固定为：

- `source_engine.py`
  - 只保留 stage orchestration 和上下文准备
- thin coordinator/adapter
  - 只保留 fetch outcome -> summary -> detector seam 相关逻辑

### 20.5 决策 4：detector live seam 的最小可接入点

#### 方案 A：`source_engine.py` 内一个极小 helper 调用

优点：

- stage context 获取最直接

缺点：

- 仍然容易让 seam 逻辑继续长在 `source_engine.py` 本体里

风险：

- 随着下一轮推进会逐步演变成厚 orchestrator

#### 方案 B：`source_engine.py` 邻接的 future thin adapter/coordinator seam

优点：

- 最符合 3-B.8 已固定方向
- 最有利于保留 stage context
- 不污染 transport
- 不污染 parser
- 最易独立回退

缺点：

- 需要下一轮继续把这个 seam skeleton 的内部结构定小

风险：

- 若没有继续强约束，仍可能长胖

#### 方案 C：`fetch_service.py` seam

优点：

- 最接近 transport outcome

缺点：

- 与当前分层方向冲突
- 既没有稳定 stage context，又会污染 transport

风险：

- 破坏 `fetch_service.py` 作为 leaf transport 的边界

#### 推荐结论

推荐 **方案 B**。

原因：

- 它最能同时满足：
  - 保存 stage context
  - 不污染 transport
  - 不污染 parser
  - 支持独立回退

不推荐方案 A：

- 因为 helper 仍然会长在 `source_engine.py` 本体里

不推荐方案 C：

- 因为 `fetch_service.py` 仍然不适合直接承担 detector seam adapter 责任

### 20.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 seam 文档设计

优点：

- 最保守

缺点：

- 3-B.8 与 3-B.9 已经把高层 seam 方向和最小 contract 基本钉清
- 继续停在纯文档层，新增收益开始下降

风险：

- 容易重复决策，不再产生新的可执行收敛

#### 方案 B：进入最小 live seam skeleton 实现

优点：

- 仍然不接 live hook
- 仍然不改 `fetch_service.py` live 行为
- 但能把下一轮推进到最小内部结构：
  - summary schema
  - base/success/error contract
  - thin adapter/coordinator schema 占位

缺点：

- 需要非常严格限制范围

风险：

- 若实现范围失控，会误滑向 live seam runtime

#### 方案 C：直接进入 detector live hook 最小骨架实装

优点：

- 推进最快

缺点：

- 当前仍缺：
  - summary/adapter contract 的代码骨架
  - dual-path fixture/test shape
  - no-regression 保护

风险：

- 直接越界进入 live detector runtime

#### 推荐结论

推荐 **方案 B**。

下一轮若推进，最小不可再小的集合应固定为：

- `FetchOutcomeSummaryBase`
- `FetchSuccessSummary`
- `FetchErrorSummary`
- future thin coordinator/adapter 的最小内部 schema / helper contract
- 对应纯内部、纯单测的 dual-path fixture / contract tests

下一轮仍然 **不允许**：

- live hook
- `fetch_service.py` 行为修改
- `source_engine.py` live detector 接入
- challenge/gateway live detection

因此下一轮建议阶段名为：

- **Phase 3-B.10：detector live seam skeleton 最小内部结构实装**

### 20.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**

原因：

- 当前 success / error 双路径的最小 contract 已经可以在文档层固定
- 当前 thin coordinator/adapter 的最小边界已经可以在文档层固定
- 当前已经足够为下一轮的最小内部结构实装提供边界

#### Step 2：如果主张本轮必须落代码，是否已有充分证明

结论：**没有**

当前仍然无法证明：

- 不落代码会阻塞本轮
- 需要落的代码已经小到不可再小
- 新增结构不会构成 live detector runtime
- 新增结构不会影响既有链路

因此 3-B.9 仍应停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 live seam skeleton 代码实装。

## 21. 3-B.10 detector live seam skeleton 最小内部结构实装结论

### 21.1 当前已落地什么

当前仓库已经以纯内部、纯非 live、纯可单测的方式落地了：

- `FetchOutcomeSummaryBase`
- `FetchSuccessSummary`
- `FetchErrorSummary`
- future thin coordinator/adapter 会依赖的最小 helper skeleton
- dual-path fixtures
- contract-level tests

当前实际代码落点为：

- `backend/app/schemas/online_live_seam.py`
- `backend/app/services/online/live_seam_skeleton.py`
- `backend/tests/fixtures/online_detector_live_seam_samples.json`
- `backend/tests/test_online_detector_live_seam_contract.py`

### 21.2 当前推荐的最小内部 contract

当前 summary contract 继续固定为：

- shared required fields:
  - `stage`
  - `expected_response_type`
  - `requested_url`
  - `fetch_outcome_kind`
- optional fields:
  - `final_url`
  - `status_code`
  - `content_type`
  - `redirected`
  - `body_text_preview`
  - `body_text_length`
  - `exception_kind`

当前 success / error 双路径的关系继续固定为：

- `FetchOutcomeSummaryBase`
  - 只表达最小共享字段
- `FetchSuccessSummary`
  - 只表达 success path
  - 不伪造 `exception_kind`
- `FetchErrorSummary`
  - 只表达 error path
  - `http_error` 至少要求 `status_code`
  - `transport_error` 至少要求 `exception_kind`

### 21.3 当前 helper skeleton 的边界

当前 helper 只允许做：

- 内部 stub / fixture / plain mapping -> summary normalization
- dual-path contract coercion

当前 helper 明确 **不** 做：

- live `httpx.Response` 提取
- live exception 提取
- detector 调度
- detector 分类
- runtime error surface 映射

因此当前 helper 的正确口径是：

- seam skeleton helper
- not live adapter

### 21.4 当前没有落地什么

当前仍然 **没有** 落地：

- exception-to-summary live adapter
- detector live hook
- `fetch_service.py` 中的 seam 接入
- `source_engine.py` 中的 seam 接入
- `response_guard_service.py` 中的 seam 接入
- challenge/gateway live detection
- browser/js-required live detection

### 21.5 当前仍然不支持什么

当前仍必须明确表述为 **不支持**：

- detector live runtime
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 21.6 为什么这仍然不等于 live runtime

因为本轮新增结构只运行在：

- 内部 schema
- 内部 helper skeleton
- fixtures
- 单元测试

它当前 **不**：

- 消费 live fetch path
- 消费 live source_engine path
- 改变现有 router / importer / DB / frontend 行为
- surface 任何 detector runtime error

因此本轮正确口径必须是：

> seam skeleton implemented internally, live detector still not connected

### 21.7 下一步最小任务

在 3-B.10 之后，最小的下一步建议应是：

- **Phase 3-B.11：detector live seam adapter 接入前决策轮**

该轮只应继续回答：

- minimal internal summary/helper 如何映射到 future adapter/coordinator
- 哪些 internal structures 已经足以支撑接入前决策
- 哪些仍不能碰 live hook

在这一步之前，仍不应直接进入：

- live hook
- `fetch_service.py` 行为修改
- `source_engine.py` detector 接入
- anti-bot bypass

## 22. 3-B.11 detector live seam adapter 接入前决策轮结论

### 22.1 当前 future adapter 还缺什么

在 3-B.10 之后，仓库已经具备：

- dual-path summary contract
- 最小 contract helper skeleton
- dual-path fixtures
- contract tests

这说明 future adapter 的输入侧 contract 已经不再停留在纯文档层。

但当前 future adapter 仍然缺少以下关键冻结项：

- 它到底负责什么、不负责什么
- 它与 `source_engine.py`、`fetch_service.py`、`response_guard_service.py`、detector skeleton 的单向边界
- 它的输出是：
  - detector classification result
  - 还是已经包含 runtime error surface 决策
- 它在进入实现前，哪些门槛已经满足，哪些仍然明显未满足

因此本轮最重要的仍然不是写 adapter，而是先钉 adapter responsibility boundary。

### 22.2 决策 1：future adapter 的职责边界

#### 方案 A：adapter 只做 summary/detector contract 衔接

优点：

- 单责最清晰
- 最符合当前 3-B 的阶段目标
- 最利于独立回退

缺点：

- 需要上层后续再决定 runtime error surface
- 看起来推进较慢

风险：

- 若后续层次继续不清，调用方可能试图把别的职责再塞回来

#### 方案 B：adapter 同时承担部分 runtime error surface 决策

优点：

- 后续看起来更接近“可上线”

缺点：

- 会提前把 classification 层和 runtime surface 层混在一起
- 会让错误码升级时机失真

风险：

- 容易误导为 live detector 已接通

#### 方案 C：adapter 承担更广的 orchestration 职责

优点：

- 表面上“一层做完很多事”

缺点：

- 会直接长成新的 orchestrator
- 与 3-B 的最小接缝目标冲突

风险：

- 边界污染风险最高
- 几乎不可控地滑向 retry/fallback/bypass 方向

#### 推荐结论

推荐 **方案 A**。

future live seam adapter 最小职责只应包括：

1. 接收 success/error 路径的内部 summary
2. 做最小 detector-ready normalization
3. 组装 detector input
4. 调用 detector
5. 返回 classification result 给上层

它当前 **不应** 负责：

- transport retry
- response_guard 逻辑
- parser/content_parse
- runtime 错误 surface 最终决策
- browser/js fallback
- anti-bot bypass

不推荐方案 B 的原因：

- 会过早混入 runtime error surface 决策

不推荐方案 C 的原因：

- 会直接把 adapter 变成新 orchestrator

### 22.3 决策 2：adapter 与现有层的最小边界

#### 方案 A：adapter 只由 `source_engine.py` 调用

优点：

- stage context 最稳定
- 最符合现有 fetch -> parser seam
- 最利于保持单向依赖

缺点：

- 需要继续严格限制 adapter 本身不要膨胀

风险：

- 若未来边界不守住，`source_engine.py` 可能继续被拖厚

#### 方案 B：adapter 直接嵌入 `fetch_service.py`

优点：

- 最靠近 transport outcome

缺点：

- `fetch_service.py` 没有稳定 stage context
- 会污染 transport 叶子层

风险：

- 破坏 `fetch_service.py` 的 leaf transport 边界

#### 方案 C：adapter 融入 `response_guard_service.py`

优点：

- 看起来靠近 response classification

缺点：

- `response_guard_service.py` 当前只应停在 generic classification
- detector/stage-aware summary 逻辑与 response_guard 的职责不同

风险：

- `response_guard_service.py` 会膨胀成 adapter + detector 前置层

#### 推荐结论

推荐 **方案 A**。

future adapter 与各层边界应固定为：

- `fetch_service.py`
  - 只输出 transport outcome
  - 不反向依赖 adapter
- `response_guard_service.py`
  - 只输出 generic classification
  - 不反向依赖 adapter
- `source_engine.py`
  - 只作为上层发起者调用 adapter
  - 不把 adapter 逻辑内嵌到 fetch 或 parser 中
- detector skeleton / future detector
  - 只消费 adapter 交给它的 normalized detector input

必须禁止的调用关系：

- `fetch_service.py -> adapter`
- `response_guard_service.py -> adapter`
- `detector -> adapter`
- `parser/content_parse -> adapter`

### 22.4 决策 3：adapter 输入输出 contract 是否已经足够

#### 方案 A：现有 contract 已足够，下一轮可进入最小 skeleton

优点：

- 与当前仓库证据最一致
- 能让项目继续以最小步推进

缺点：

- 仍不表示 live 接入条件已经满足

风险：

- 若表述不准，容易被误读为“可以直接接 live”

#### 方案 B：还需补少量 contract 字段/状态后再进入

优点：

- 更保守

缺点：

- 当前没有明显证据表明还缺关键字段
- 容易重复 3-B.9 / 3-B.10 已完成的工作

风险：

- 文档轮重复，信息增量低

#### 方案 C：当前 contract 仍不足，下一轮继续停在设计层

优点：

- 最保守

缺点：

- 与当前仓库实际状态不符
- 已有内部 schema/helper/fixtures/tests 说明 contract 层已不是纯概念

风险：

- 项目推进无效停滞

#### 推荐结论

推荐 **方案 A**。

当前证据表明：

- `FetchOutcomeSummaryBase / FetchSuccessSummary / FetchErrorSummary`
  - 已足够作为 future adapter 输入基础
- 当前 detector input/result contract
  - 已足够承接 future adapter 输出侧的 classification-only contract

当前仍然不足以支持的内容是：

- adapter 到 runtime error surface 的关系
- adapter 到 live wiring 的关系
- adapter 进入 live path 之后的 no-regression 证明

因此结论应是：

- 当前 contract 已足够支持“最小 adapter skeleton”
- 但还不足够支持“adapter live 接入”

### 22.5 决策 4：错误码升级门槛与接入前门槛

#### 方案 A：adapter skeleton 一落地就允许升级部分 detector 错误码

优点：

- 状态推进快

缺点：

- 会把 internal skeleton 误写成 live runtime 支持

风险：

- 阶段误导风险最高

#### 方案 B：必须等 live adapter 接通且可稳定触发才升级

优点：

- 与当前分层最一致
- 能保持 `skeleton_modeled / seam_modeled / runtime-implemented` 三层区分

缺点：

- 状态升级更保守

风险：

- 需要后续 live 接入测试矩阵配合

#### 方案 C：等完整 detector runtime 才升级

优点：

- 最保守

缺点：

- 会压平分阶段推进的价值

风险：

- Traceability 对阶段推进的帮助下降

#### 推荐结论

推荐 **方案 B**。

adapter 接入前必须满足的条件至少包括：

1. live seam 位置固定
2. dual-path summary 可稳定构造
3. adapter contract 已冻结
4. detector 输出与 error surface 的关系已明确
5. 正负样本与测试矩阵足够

当前已满足的部分：

- live seam 位置基本固定
- dual-path summary 已稳定建模
- adapter 输入输出 contract 已基本足够

当前仍明显未满足的部分：

- adapter live wiring 未存在
- detector 输出与 runtime error surface 关系未冻结
- live path 触发与 no-regression 证据不存在

因此 challenge/gateway 错误码当前仍然不得升级。

### 22.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 adapter 文档设计

优点：

- 最保守

缺点：

- 当前边界与 contract 已经足够清晰
- 再做纯文档轮，新增收益开始很低

风险：

- 重复 3-B.11 结论

#### 方案 B：进入最小 adapter skeleton 实现

优点：

- 仍然不接 live path
- 仍然不改 fetch/source/response_guard 行为
- 能把下一轮推进到 adapter 自身最小内部结构

缺点：

- 需要极严范围控制

风险：

- 若范围失控，会误滑向 adapter live 接入

#### 方案 C：直接进入 detector live seam adapter 接入实装

优点：

- 推进快

缺点：

- 当前仍缺 runtime error surface 冻结
- 当前仍缺 live no-regression 设计
- 当前仍缺 adapter 接入后的最小回退策略证明

风险：

- 直接越界进入 live runtime

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- future adapter 内部 input contract
- future adapter 内部 output contract
- no-op adapter skeleton
- 纯内部 adapter fixture / tests
- 明确的“未接 live path”边界测试

下一轮建议阶段名为：

- **Phase 3-B.12：detector live seam adapter 最小内部 skeleton 实装**

### 22.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**

原因：

- 当前 future adapter 的职责边界已经可以基于仓库证据固定
- 当前 adapter 与现有层的单向边界已经可以固定
- 当前已经足够决定下一轮是否可以进入最小 adapter skeleton

#### Step 2：如果主张本轮必须落代码，是否已有充分证明

结论：**没有**

当前无法证明：

- 不落代码会阻塞本轮
- 需要落的代码已小到不可再小
- 新增代码不会构成 adapter live 接入
- 新增代码不会影响既有链路

因此 3-B.11 仍应停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 adapter 接入实装。

## 23. 3-B.12 detector live seam adapter 最小内部 skeleton 实装结论

### 23.1 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可单测的方式落地了：

- `DetectorAdapterInput`
- `DetectorAdapterOutput`
- `DetectorAdapterOutcome`
- adapter no-op helper skeleton
- adapter fixtures
- adapter contract / no-op tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_adapter.py`
- `backend/app/services/online/detector_adapter_skeleton.py`
- `backend/tests/fixtures/online_detector_adapter_samples.json`
- `backend/tests/test_online_detector_adapter_contract.py`

### 23.2 当前 adapter contract 的最小范围

当前 adapter input contract 只承载：

- `stage`
- `expected_response_type`
- `fetch_outcome_summary`

其中：

- `fetch_outcome_summary`
  - 仍然只能是：
    - `FetchSuccessSummary`
    - `FetchErrorSummary`

当前 adapter output contract 只承载三种内部状态：

- `noop`
- `detector_input_prepared`
- `detector_result_attached`

它当前明确 **不** 承载：

- runtime error surface
- retry/fallback decision
- browser/js escalation
- parser/runtime orchestration

### 23.3 当前 no-op helper 的边界

当前 no-op helper 只允许做：

- summary -> adapter input 的准备
- adapter output contract 的 no-op/contract coercion

当前 no-op helper 明确 **不** 做：

- live wiring
- runtime dispatch
- error surface mapping
- parser 协调
- live detector 调用

因此本轮 helper 的正确口径必须是：

- adapter skeleton helper
- not live adapter

### 23.4 当前没有落地什么

当前仍然 **没有** 落地：

- live seam adapter 接入
- `source_engine.py` 中的 adapter 调用
- `fetch_service.py` 中的 adapter 接入
- `response_guard_service.py` 中的 adapter 接入
- challenge/gateway live detection
- browser/js-required live detection

### 23.5 当前仍然不支持什么

当前仍必须明确表述为 **不支持**：

- detector live runtime
- detector live seam adapter 接入
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 23.6 为什么这仍然不等于 live adapter

因为本轮新增结构只运行在：

- 内部 schema
- 内部 no-op helper
- fixtures
- 单元测试

它当前 **不**：

- 消费 live fetch/source/response_guard 路径
- 改变现有 router / importer / DB / frontend 行为
- 触发任何 runtime detector wiring
- 触发任何 runtime error surface

因此本轮正确口径必须是：

> adapter skeleton implemented internally, adapter still not connected to live runtime

### 23.7 下一步最小任务

在 3-B.12 之后，最小的下一步建议应是：

- **Phase 3-B.13：detector live seam adapter 最小接入决策轮**

该轮只应继续回答：

- adapter internal skeleton 与 future live wiring 的最小映射关系
- 哪些 adapter 内部结构已经足够支撑接入前决策
- 哪些层次仍然不能碰 live path

在这一步之前，仍不应直接进入：

- live adapter 接入
- `source_engine.py` detector 调用
- `fetch_service.py` 行为修改
- anti-bot bypass

## 24. 3-B.13 detector live seam adapter 最小接入决策轮结论

### 24.1 当前 future minimal live entry 还缺什么

在 3-B.12 之后，仓库已经具备：

- dual-path live seam summary contract
- adapter input/output internal contract
- adapter no-op helper
- adapter / live seam fixtures 与 contract tests

这些结构已经足够支撑本轮做“future minimal live entry”决策。

当前真正还缺的不是代码，而是以下边界冻结：

- “minimal live entry” 到底只算内部 no-op wiring，还是已经算 live detector 接入
- future 最小 wiring 点到底落在 `source_engine.py` 本体、`source_engine.py` 邻接 thin helper，还是 `fetch_service.py`
- adapter 接入后哪些行为只允许内部观察，哪些行为仍然绝对禁止
- challenge / gateway 错误码在 future minimal live entry 后是否能升级，以及升级门槛到底是什么

因此本轮正确动作仍然是：

- 先把 minimal live-entry boundary 写死
- 先把 allowed / disallowed behaviors 写死
- 先把错误码升级门槛写死
- 默认不进入 adapter live 接入

### 24.2 决策 1：future adapter 的“最小接入”到底是什么

#### 方案 A：只允许内部 no-op wiring + internal observation

优点：

- 与当前 `FetchSuccessSummary` / `FetchErrorSummary` 和 `DetectorAdapterInput` / `DetectorAdapterOutput` 的真实仓库状态最一致
- 最不容易把 adapter import / 调用误写成“detector 已上线”
- 最利于下一轮小步落“可回退、零行为变化”的 live-entry skeleton

缺点：

- 不能证明 detector 错误码已能靠近 runtime surface
- 对调试可见性仍然较克制

风险：

- 如果文档措辞不严，内部观察仍可能被误读为“线上已能识别 challenge/gateway”

#### 方案 B：允许 internal observation + internal surfaced classification

优点：

- 能更明确表达 live path 已经看到了 detector result
- 对 future trace/debug 看起来更直观

缺点：

- “internal surfaced” 与“runtime surfaced”边界很容易被混写
- 会把 3-B.13 从接入决策轮推向 error-surface 决策轮

风险：

- 最容易诱发新增术语膨胀，并让后续 AI 误把 classification result 当成 public behavior

#### 方案 C：允许小范围影响 runtime behavior

优点：

- 推进速度最快

缺点：

- 直接越过本轮边界
- 等价于提前进入 adapter live 接入实装

风险：

- 会把“minimal live entry”误写成“detector live runtime 已支持”

#### 推荐结论

推荐 **方案 A**。

本轮将 “future minimal live entry” 固定定义为：

- 仅允许在 future 某个非 public 的 live seam 点调用 adapter
- 仅允许构造 `DetectorAdapterInput`
- 仅允许获得 `DetectorAdapterOutput`
- 仅允许在内部调试、断言、测试或 trace 语义中观察 `detector_result` / `recommended_error_code`

它当前明确 **不意味着**：

- runtime error surface 已改变
- detector 已正式参与产品行为
- challenge/gateway 已能对外稳定识别
- detector 已与 parser / fallback / browser / JS 路径联动

不推荐方案 B 的原因：

- 会额外引入“internal surfaced”这类容易扩散的中间语义

不推荐方案 C 的原因：

- 已经超出 3-B.13 的决策轮边界

### 24.3 决策 2：最小 wiring 点到底在哪里

#### 方案 A：在 `source_engine.py` 内部放极小调用点

优点：

- stage context 现成
- 位置直观，处于 `fetch -> parser` 之间

缺点：

- 容易继续把 `source_engine.py` 写胖
- minimal live-entry 细节会直接和现有 preview/discovery 编排混在一起

风险：

- 若后续再叠加 detector dispatch / error mapping，`source_engine.py` 会快速长成大杂烩

#### 方案 B：放在 `source_engine.py` 邻接的 future thin helper/coordinator

优点：

- 逻辑位置仍然 anchored 在 `source_engine.py` seam
- 实际职责可以保持为一个薄中间层
- 既能拿到 stage context，又能避免污染 `fetch_service.py` / parser
- 最利于下一轮单独回退

缺点：

- 需要新增一个更明确的 future helper/coordinator 概念
- 下一轮必须继续严格控制该 helper 只做 no-op live-entry skeleton

风险：

- 如果 helper 过重，会演变成新的 runtime coordinator

#### 方案 C：在 `fetch_service.py` 内部加 hook

优点：

- 最早拿到 transport response / exception

缺点：

- `fetch_service.py` 当前是 leaf transport，不持有 stage context
- 会把 transport/generic response_guard 与 detector seam 混成一层
- 容易把 `fetch_service.py` 变成“业务前置分发器”

风险：

- 一旦从这里起步，challenge/gateway/browser/js 检测很容易继续反向污染 transport 层

#### 推荐结论

推荐 **方案 B**。

本轮固定结论为：

- future 最小 wiring 点逻辑上仍位于 `source_engine.py` 所在的 `fetch_stage_response(...)` 之后、`parse_*_preview(...)` 之前
- 但实际实现更推荐由 `source_engine.py` 调用一个邻接的 thin helper/coordinator
- `fetch_service.py` 继续只负责 transport + generic response_guard
- parser / content_parse 继续只负责解析，不承担 live-entry seam

不推荐方案 A 的原因：

- 它的逻辑位置是对的，但把细节直接堆进 `source_engine.py` 会放大维护成本

不推荐方案 C 的原因：

- `fetch_service.py` 仍然不应成为 detector wiring 点

### 24.4 决策 3：接入后允许发生什么，不允许发生什么

#### 方案 A：只允许 internal observation

优点：

- 最符合本轮“只定义最小接入，不定义 runtime behavior”目标
- 与现有 adapter no-op skeleton 的边界自然衔接
- 对 Traceability 和回退都最友好

缺点：

- 不能提前验证 detector result 如何靠近 runtime

风险：

- 需要明确“internal observation”仅限内部 trace / assert / test，不进入 public behavior

#### 方案 B：允许 internal surfaced result，但不改 public behavior

优点：

- 能让下一轮更容易观察 live path 中的 adapter result

缺点：

- “surfaced” 一词本身就容易造成阶段误导
- 会逼近 runtime error surface mapping 讨论

风险：

- 容易被后续 AI 写成“detector result 已进入上层控制流”

#### 方案 C：允许 detector result 直接影响上层控制流

优点：

- 表面上推进最快

缺点：

- 直接跨入 live adapter 接入甚至 detector live runtime
- 会让 response_guard / parser / fallback 边界同时失稳

风险：

- public behavior 漂移
- 回退困难

#### 推荐结论

推荐 **方案 A**。

future minimal live entry 后，当前只允许：

- 内部构造 `DetectorAdapterInput`
- 内部拿到 `DetectorAdapterOutput`
- 内部记录、断言或调试级观察 `detector_result` / `recommended_error_code`

future minimal live entry 后，当前仍然明确 **不允许**：

- 直接改变 API 输出
- 直接抛 detector 错误码给上层
- 直接触发 fallback / browser / JS 路径
- 直接替代 `response_guard_service.py`
- 直接影响 parser / content_parse

这些禁止项应继续通过两类方式钉住：

- 文档口径：明确写“minimal live entry != live detector runtime”
- 边界测试：明确证明 `fetch_service.py` / `response_guard_service.py` / parser 路径不感知 adapter 结果

不推荐方案 B 的原因：

- 它已经开始把内部结果推近上层控制流

不推荐方案 C 的原因：

- 已经不再是 3-B.13 的“最小接入决策”

### 24.5 决策 4：错误码何时才能更靠近 runtime

#### 方案 A：minimal live entry 一接通就升级部分 detector 错误码

优点：

- 口径简单

缺点：

- 会把 future adapter 调用误写成 runtime actually raises
- 与当前 `adapter_modeled` 的真实语义冲突

风险：

- 最容易把 challenge/gateway 写成“已支持线上识别”

#### 方案 B：引入新的 `internal_observed` 生命周期状态

优点：

- 能表达“比 adapter_modeled 更靠近 live，但仍未 runtime-implemented”

缺点：

- 当前生命周期术语已经较多
- 新状态会增加文档和 Traceability 认知负担

风险：

- 若没有真实 live wiring 证据，新增状态只会让术语体系更混乱

#### 方案 C：只有真正 live runtime 行为可稳定复现后才升级

优点：

- 与当前仓库证据最一致
- 最能防止“接入”被误写成“正式支持”
- 与现有 `adapter_modeled -> runtime-implemented` 口径最一致

缺点：

- detector 错误码状态提升会更保守

风险：

- 需要在后续 live-entry skeleton 轮里继续接受“状态暂不升级”的约束

#### 推荐结论

推荐 **方案 C**。

本轮明确固定：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

即使 future minimal live entry 落地，当前也 **不应仅因 adapter 被调用** 就从：

- `adapter_modeled`

升级为：

- `runtime-implemented`

本轮同时不推荐新增正式生命周期状态 `internal_observed`。更保守、也更清晰的写法是：

- future minimal live entry 最多只允许“在内部观察 recommended_error_code”
- 但错误码生命周期状态继续保持不变

只有同时满足以下条件后，challenge/gateway 才有资格 future 升级：

1. live-entry helper 已真实存在
2. live path 能稳定调用 adapter
3. live path 中的 detector result 与 runtime error surface 关系已冻结
4. 正样本、负样本与 no-regression 证明都存在
5. 文档、Traceability、测试与错误码状态仍明确区分：
   - classification only
   - not bypass
   - not browser/js runtime support

不推荐方案 A 的原因：

- 会直接破坏当前错误码文档的可信度

不推荐方案 B 的原因：

- 当前不足以证明必须引入新生命周期状态

### 24.6 决策 5：下一轮最小可执行任务是什么

#### 方案 A：继续只做 live-entry 文档设计

优点：

- 最保守

缺点：

- 当前边界已经足够清楚，再做一轮纯文档会明显重复 3-B.13

风险：

- 继续拖慢进入最小 no-op wiring 验证的节奏

#### 方案 B：进入 minimal live-entry skeleton 实现（仅内部 no-op wiring）

优点：

- 仍然不进入 adapter live 接入
- 能把本轮文档结论收敛成最小可验证内部结构
- 最利于证明“live path 可调用 adapter，但 public behavior 仍零变化”

缺点：

- 需要非常严格的范围控制

风险：

- 如果把内部观察写成上层行为，就会滑向 live adapter 接入

#### 方案 C：直接进入 detector adapter 最小 live 接入实装

优点：

- 推进速度最快

缺点：

- 当前仍缺 runtime error surface 冻结
- 当前仍缺 live no-regression 设计
- 当前仍缺“adapter 结果如何不影响 parser / response_guard”的实证

风险：

- 直接越界进入 detector live runtime

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 `source_engine.py` 邻接的 thin live-entry helper/coordinator
- 仅在内部 live seam 点做 no-op adapter 调用
- 仅允许内部构造 `DetectorAdapterInput`
- 仅允许内部拿到 `DetectorAdapterOutput`
- 仅允许内部 observation，不改变任何 public behavior
- 边界测试必须继续证明：
  - 不改 `fetch_service.py` 行为
  - 不改 `response_guard_service.py` 行为
  - 不改 parser / content_parse 行为
  - 不 surface detector 错误码

下一轮建议阶段名为：

- **Phase 3-B.14：detector live seam adapter 最小 live-entry skeleton 实现**

当前不推荐直接进入真正 live 接入，原因是：

- 仍缺 runtime error surface 冻结
- 仍缺 public no-behavior-change 证据
- 仍缺 challenge/gateway live 触发与回归证明

### 24.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前 internal seam skeleton 与 adapter skeleton 已足够支撑 3-B.13 决策
- 本轮真正缺的是 live-entry boundary，而不是新增代码
- 本轮已经足以决定下一轮能否安全进入 minimal live-entry skeleton

#### Step 2：如果主张本轮必须落代码，是否已有充分证明

结论：**没有**。

当前无法证明：

- 不落代码会阻塞 3-B.13
- 需要落的代码已小到不可再小
- 新增代码不会构成 adapter live 接入
- 新增代码不会影响既有 fetch/source/parser 链路

因此 3-B.13 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 detector live seam adapter 接入实装。

## 25. 3-B.14 detector live seam adapter 最小 live-entry skeleton 实现结论

### 25.1 当前最小 live-entry skeleton 落点

按 3-B.13 已冻结的边界，本轮最小 live-entry skeleton 的代码落点固定为：

- `backend/app/services/online/detector_live_entry_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `detector_live_entry_skeleton.py`
  - 只负责内部 summary -> adapter input/output -> detector result 的 no-op wiring
- `source_engine.py`
  - 只在 `fetch_stage_response(...)` 之后、parser 之前做一次邻接 seam 调用
  - 调用结果仅停留在内部 observation，不进入返回值或异常 surface

本轮没有把 wiring 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 25.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- success path live-entry helper
- error path live-entry helper
- summary -> adapter input/output 的 live-path 内部组装
- 在 summary 信息足够时的 detector skeleton 内部 observation
- `source_engine.py` 邻接 seam 的最小 no-op 调用点
- live-entry fixtures
- live-entry wiring / no-behavior-change / boundary tests

当前实际代码落点为：

- `backend/app/services/online/detector_live_entry_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_live_entry_samples.json`
- `backend/tests/test_online_detector_live_entry_skeleton.py`

### 25.3 当前 live-entry skeleton 允许做到什么

本轮当前只允许做到：

- 内部构造 `FetchSuccessSummary` / `FetchErrorSummary`
- 内部构造 `DetectorAdapterInput`
- 内部获得 `DetectorAdapterOutput`
- 在 summary 字段足够时，内部获得 detector skeleton 的 `classification result`
- 在 `source_engine.py` 中以局部变量/局部 no-op 调用的形式完成 observation

### 25.4 当前 live-entry skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- detector live runtime
- adapter live 接入对外行为
- runtime error surface 变化
- API 输出变化
- parser / content_parse 输入变化
- response_guard 行为变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- detector adapter live 接入
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 25.5 为什么这仍然不等于 live detector runtime

因为本轮新增 wiring 只做：

- internal no-op wiring
- internal observation

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 live-entry helper 调用还加了内部 no-op guard：

- 即便 live-entry helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal live-entry skeleton implemented internally, external behavior remains unchanged

### 25.6 错误码状态结论

本轮没有新增 detector 错误码生命周期状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

原因：

- 这轮只是 internal live-entry skeleton
- 不是 runtime error surface 接通
- 不是 public behavior 改写

因此本轮不引入：

- `live-entry-modeled`
- `runtime-implemented`

### 25.7 下一步最小任务

在 3-B.14 之后，最小的下一步建议应是：

- **Phase 3-B.15：detector live behavior gating 决策轮**

该轮只应继续回答：

- 当前 internal observation 哪些 future 可以进入更靠近 runtime 的 gating
- 哪些 detector result 仍必须继续停在 internal-only
- runtime error surface / public behavior 升级前还差哪些门槛
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- adapter live 接入对外生效
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 26. 3-B.15 detector live behavior gating 决策轮结论

### 26.1 当前 future behavior gating 还缺什么

在 3-B.14 之后，仓库已经具备：

- detector static skeleton
- live seam summary contract
- adapter internal skeleton
- minimal live-entry skeleton
- `source_engine.py` 邻接 seam 的 internal observation 调用点

这意味着当前仓库已经能够证明：

- detector result 可以在 live path 内部被构造
- 但 detector result 仍然只停留在 internal observation
- 外部返回值、异常、parser、response_guard 仍然完全不感知这些结果

当前真正还缺的不是代码，而是以下 gating 边界冻结：

- behavior gating 到底只是“内部信号上浮”，还是已经意味着 runtime 行为变化
- detector result 如果 future 被更高一层看到，最小安全上限到底是哪一层
- 哪些行为可以被 detector gate 感知，哪些行为一旦开放就已经不是 gating，而是 runtime behavior change
- challenge/gateway 错误码在 future gating 后是否能更靠近 runtime，以及门槛到底是什么

因此本轮最重要的不是继续写代码，而是先把 behavior gating 的定义、上限和禁止项写死。

### 26.2 决策 1：behavior gating 到底是什么

#### 方案 A：只允许 internal observation -> internal signal 的 no-op gating

优点：

- 最符合当前仓库已存在的 internal observation 事实
- 最容易和 3-B.14 的 no-behavior-change 边界对齐
- 最利于下一轮继续以纯内部、纯可回退方式推进

缺点：

- 仍然不能证明 detector result 如何靠近 runtime surface
- 对 future gate 层的形状描述会更抽象

风险：

- 如果不把“internal signal”讲清楚，后续 AI 仍可能把它写成行为已生效

#### 方案 B：允许 detector result 到达更靠近 runtime 的内部 surfaced 层

优点：

- 比单纯 observation 更接近 future gating 真实目标
- 能帮助 future 明确“哪个内部 decision point 第一次拿到 detector result”

缺点：

- “internal surfaced” 一词容易被混写成“对外 surfaced”
- 如果没有强约束，容易继续滑向 runtime-visible behavior

风险：

- 最容易引发术语漂移

#### 方案 C：允许 detector result 小范围改变外部行为

优点：

- 推进最快

缺点：

- 已经不再是 gating 决策，而是 runtime behavior 变更决策
- 会直接越过当前阶段边界

风险：

- 极易被误写成 detector 已上线

#### 推荐结论

推荐 **方案 A**，同时在文档层显式定义一个 future gate-layer 概念：

- behavior gating 只意味着：
  - future 某个内部 decision point 可以接收到 detector result 派生出的 internal signal
  - future 可以基于门控条件决定“是否允许继续携带这个 internal signal”
- behavior gating **不意味着**：
  - API 输出变化
  - 异常 surface 变化
  - browser/js/fallback 被触发
  - parser / response_guard 被 detector 改写

这里的 “gating” 应定义为：

- detector result 从 internal observation 到更高一层 internal signal carrying 的门
- 而不是 public behavior change 的门

不推荐方案 B 的原因：

- 它可以作为概念存在，但当前不应直接作为实现目标

不推荐方案 C 的原因：

- 已经越过 3-B.15 的决策边界

### 26.3 决策 2：future detector 结果最小可影响层级

#### 方案 A：停在 internal observation

优点：

- 最保守
- 与 3-B.14 当前仓库状态完全一致

缺点：

- 不能回答 future gating 到底 first touches 哪一层

风险：

- 下一轮容易再次重复“仅 observation”的结论

#### 方案 B：允许 internal surfaced signal

优点：

- 能清楚区分：
  - 当前 helper/local discard observation
  - future gate-layer internal signal carrying
- 能为下一轮 minimal gating skeleton 提供最小清晰入口

缺点：

- 需要非常明确写清它不是 runtime-visible surface

风险：

- 如果被拿来当错误码生命周期状态，会引入术语混乱

#### 方案 C：允许试探接近 runtime error surface

优点：

- 最接近 future public behavior

缺点：

- 当前缺少 gating 与 error-surface 关系冻结
- 当前缺少 public no-regression 证据

风险：

- 会直接把 3-B.15 写成 behavior 已开始生效

#### 推荐结论

推荐 **方案 B**，但必须加两个硬约束：

1. `internal surfaced signal` 只作为 future gate-layer contract 概念存在
2. 它不是新的错误码生命周期状态，更不是 `runtime-implemented`

因此当前最安全的上限应固定为：

- future detector result 最多先传播到 `internal surfaced signal`
- 当前阶段明确禁止继续跨到：
  - runtime error surface
  - public behavior layer

不推荐方案 A 的原因：

- 它过于保守，不足以为下一轮 minimal gating skeleton 提供清晰收敛目标

不推荐方案 C 的原因：

- 当前证据不足以支持试探 runtime-visible 层

### 26.4 决策 3：允许被 gating 的行为与绝对禁止的行为

#### 方案 A：只允许内部记录与内部 contract 传播

优点：

- 最符合当前阶段边界
- 最利于文档与测试继续钉死 no-behavior-change

缺点：

- 看起来推进较慢

风险：

- 需要继续明确“传播”只限 internal layer

#### 方案 B：允许内部更高层感知 detector result，但不改外部行为

优点：

- 更贴近 future behavior gating 的真实用途
- 有助于下一轮定义一个专门的 internal gate decision contract

缺点：

- 如果边界不够硬，容易被继续扩写成控制流改变

风险：

- 需要更强的 no-regression 测试规划

#### 方案 C：允许 detector result 开始影响控制流

优点：

- 推进快

缺点：

- 一旦影响控制流，就已经不是“gating boundary”，而是 runtime behavior change

风险：

- 会污染 parser / response_guard / API / error surface

#### 推荐结论

推荐 **方案 B**，但仅限 internal-only 范围。

future 最小 gating 后，允许的行为最多包括：

- 内部记录 detector 命中
- 内部返回一个更明确的 internal signal/result
- 为 future error surface mapping 提供证据

此阶段绝对禁止的行为包括：

- API 输出变化
- 异常 surface 变化
- parser / content_parse 分支变化
- fallback / browser / JS 路径触发
- 自动 retry / backoff
- detector 替代 response_guard

这些禁止项应继续通过两类方式钉住：

- 文档：明确写“gating != runtime-visible behavior”
- 测试规划：继续要求 no-behavior-change / no-surface-change / no-parser-branch-change

不推荐方案 A 的原因：

- 它对下一轮 minimal gating skeleton 的指导性不够

不推荐方案 C 的原因：

- 已经越界进入 runtime behavior 变化

### 26.5 决策 4：错误码何时可以进一步靠近 runtime

#### 方案 A：gating skeleton 一落地就允许部分 detector 错误码升级

优点：

- 口径简单

缺点：

- 与当前 `adapter_modeled` 口径冲突
- 会把 gate-layer signal 误写成 runtime actually raises

风险：

- 最容易把 challenge/gateway 写成线上已支持

#### 方案 B：允许 internal surfaced，但仍不升级为 runtime-implemented

优点：

- 能承认 future gate-layer 可能比 internal observation 更进一步
- 同时保持错误码状态不越界

缺点：

- 需要把“internal surfaced”与错误码状态明确拆开

风险：

- 如果表达不清，仍会引起误读

#### 方案 C：只有真正 live behavior change 且可稳定复现后才升级

优点：

- 与当前文档体系和仓库事实最一致
- 最能防止阶段误导

缺点：

- 状态升级更保守

风险：

- 需要继续接受“错误码状态暂不升级”的约束

#### 推荐结论

推荐 **方案 C**，并补充接受 **方案 B** 的概念层结论：

- future gate-layer 可以存在 `internal surfaced signal`
- 但 challenge/gateway 错误码生命周期状态仍然 **不因此升级**

也就是说：

- `recommended only`
- `internal observed`
- `internal surfaced`

这些都只能作为 gate-layer 行为语义，不应被写成新的错误码生命周期状态。

因此 challenge/gateway 当前继续保持：

- `adapter_modeled`

只有同时满足以下条件后，才允许 future 靠近 runtime surface：

1. gate-layer 与 runtime error surface 的关系已冻结
2. public behavior change 已单独决策并小步实现
3. live path 可稳定触发对应 detector 结果
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试仍明确：
   - classification only
   - not bypass
   - not browser/js runtime support

不推荐方案 A 的原因：

- 会直接破坏错误码状态体系

不推荐方案 B 的原因：

- 如果把它误当成 lifecycle，会继续膨胀术语

### 26.6 决策 5：下一轮最小可执行任务是什么

#### 方案 A：继续只做 gating 文档设计

优点：

- 最保守

缺点：

- 当前 gating boundary 已足够清楚，继续纯文档会明显重复

风险：

- 推进停滞

#### 方案 B：进入 minimal gating skeleton 实现（仅 internal signal / no-op decision）

优点：

- 仍然不进入 runtime-visible behavior
- 能把 3-B.15 的概念边界收敛成最小内部 gate contract
- 最利于证明：
  - internal surfaced signal exists
  - external behavior still unchanged

缺点：

- 需要非常严格控制范围

风险：

- 如果把 gate decision 写成控制流改变，就会越界

#### 方案 C：直接进入 detector 结果影响 runtime 的最小实装

优点：

-
  推进最快

缺点：

- 当前仍缺 gate-layer 与 runtime error surface 的关系冻结
- 当前仍缺 public no-regression 证明
- 当前仍缺“哪些结果允许 first visible”的正式证据链

风险：

- 会直接跨进 runtime-visible behavior

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 internal gate input/result contract
- 一个 source-engine 邻接的 minimal gating helper
- 仅 internal signal carrying
- 仅 no-op gate decision
- 仍然不改返回值、不改异常、不改 parser、不改 response_guard
- 对应的 no-behavior-change / no-surface-change 测试

下一轮建议阶段名为：

- **Phase 3-B.16：detector live behavior minimal gating skeleton 实现**

当前不推荐直接进入 runtime-visible behavior，原因是：

- 仍缺 gate-layer 与 runtime surface 的明确映射
- 仍缺 public behavior 变更的独立决策轮
- 仍缺 challenge/gateway visible behavior 的稳定验证

### 26.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前 minimal live-entry skeleton 已足够证明 detector result 到达 internal observation 层
- 当前最危险的歧义是 gating 会不会被误写成 behavior 已生效
- 本轮已经足够决定下一轮能否安全进入 minimal gating skeleton

#### Step 2：如果主张本轮必须落代码，是否已有充分证明

结论：**没有**。

当前无法证明：

- 不落代码会阻塞 3-B.15
- 需要落的代码已小到不可再小
- 新增代码不会构成 runtime-visible behavior
- 新增代码不会影响既有链路

因此 3-B.15 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 behavior gating skeleton 实装。

## 27. 3-B.16 detector live behavior minimal gating skeleton 实现结论

### 27.1 当前 minimal gating skeleton 最小落点

按 3-B.15 已冻结的边界，本轮 minimal gating skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_gate.py`
- `backend/app/services/online/detector_gating_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_gate.py`
  - 只负责 internal gate input / gate result / carried signal / noop decision contract
- `detector_gating_skeleton.py`
  - 只负责 adapter output -> gate input -> gate result 的最小 no-op gating helper
- `source_engine.py`
  - 只在现有 live-entry no-op observation 之后追加一层 internal gating helper 调用
  - 调用结果继续停留在 internal-only 层

本轮没有把 gating 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 27.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorGateInput`
- `DetectorGateSignal`
- `DetectorGateResult`
- `DetectorGateOutcome`
- `DetectorGateDecision`
- minimal gating helper
- source-engine 邻接 gating no-op 调用点
- gating fixtures
- gate contract / helper / signal carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_gate.py`
- `backend/app/services/online/detector_gating_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_gating_samples.json`
- `backend/tests/test_online_detector_gating_skeleton.py`

### 27.3 当前 gating skeleton 允许做到什么

本轮当前只允许做到：

- internal gate input 被构造
- internal gate result 被构造
- detector result 被内部携带到 gate-layer
- gate helper 返回 no-op decision
- source-engine 邻接位置内部调用 gating helper

其中 current carried signal 只表达：

- detector candidate 的 internal signal carrying
- 以及对应的 recommended error code 仅作为 internal-only 信息

### 27.4 当前 gating skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime-visible gating
- detector live runtime
- runtime error surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime-visible gating
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 27.5 为什么这仍然不等于 runtime-visible gating

因为本轮新增 gating 只做：

- internal signal carrying
- no-op gate decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 gating helper 调用仍被内部 no-op guard 包裹：

- 即便 gating helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal gating skeleton implemented internally, external behavior remains unchanged

### 27.6 错误码状态结论

本轮没有新增 detector 错误码生命周期状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_observed`
- `internal_surfaced`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

### 27.7 下一步最小任务

在 3-B.16 之后，最小的下一步建议应是：

- **Phase 3-B.17：detector runtime-visible gating 决策轮**

该轮只应继续回答：

- 哪一类 internal gate result future 有资格 first become runtime-visible
- 哪些 detector result 仍必须继续停在 internal-only
- runtime-visible gating 与 error surface / API / parser 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime-visible gating 生效
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 28. 3-B.17 detector runtime-visible gating 决策轮结论

### 28.1 当前 future runtime-visible gating 还缺什么

在 3-B.16 之后，仓库已经具备：

- detector static skeleton
- live seam summary contract
- adapter internal skeleton
- minimal live-entry skeleton
- minimal gating skeleton
- `source_engine.py` 邻接 seam 的 internal signal carrying / no-op gate decision

这意味着当前仓库已经能够证明：

- detector result 可以在 live path 内部被构造
- detector result 可以进入 gate-layer internal contract
- 但 detector result 仍然没有进入更高层 runtime-visible boundary
- 外部返回值、异常、parser、response_guard 仍然完全不感知这些结果

当前真正还缺的不是代码，而是以下 runtime-visible 边界冻结：

- `runtime-visible gating` 到底只是“更高一层 internal boundary 可见”，还是已经意味着 external behavior change
- detector result 如果 future 开始变得 runtime-visible，最小安全上限到底是哪一层
- 哪些行为可以被 runtime-visible gating 感知，哪些行为一旦开放就已经不是 gating，而是 runtime behavior change
- challenge/gateway 错误码在 future runtime-visible gating 后是否能更靠近 runtime surface，以及门槛到底是什么

因此本轮最重要的不是继续写代码，而是先把 runtime-visible definition、最小可见层和禁止项写死。

### 28.2 决策 1：runtime-visible gating 的定义

#### 方案 A：只允许 internal higher-layer carrying / observation

优点：

- 最保守
- 最符合当前 3-B.16 已有 internal signal carrying 的事实
- 最不容易误导为外部行为已开始变化

缺点：

- 对下一轮的收敛目标不够明确

风险：

- 容易继续停留在“仍只是局部内部状态”，无法定义 future higher-layer boundary

#### 方案 B：允许 internal surfaced signal 到达更靠近 runtime 的 boundary

优点：

- 能明确 future 哪一层 first sees detector gate result
- 能把 runtime-visible gating 定义为“更高一层 internal boundary 可见”
- 最适合作为下一轮最小 skeleton 的清晰入口

缺点：

- 需要非常明确写清：它仍然不是 public behavior

风险：

- 如果措辞不严，后续 AI 可能把“runtime-visible”误读成“用户可见/调用方可见”

#### 方案 C：允许 detector result 小范围改变外部行为

优点：

- 推进最快

缺点：

- 已经不再是 runtime-visible gating 决策，而是 runtime behavior change 决策
- 直接越过当前阶段边界

风险：

- 最容易被误写成 detector 已正式支持

#### 推荐结论

推荐 **方案 B**。

本轮将 `runtime-visible gating` 固定定义为：

- future 某个更高一层的 internal decision boundary 可以 first see detector gate result
- detector result 不再只停留在 helper 局部变量，而进入一个更持久但仍是 internal-only 的 boundary
- 该 boundary 可以为 future runtime error surface mapping 做准备

它当前明确 **不意味着**：

- API 输出已变化
- 调用方已收到 detector 错误
- browser/js/fallback 已自动触发
- parser/content_parse 已改走新分支
- anti-bot 已被处理

不推荐方案 A 的原因：

- 它不足以为下一轮定义一个清晰的 higher-layer carrying 入口

不推荐方案 C 的原因：

- 已经越过 3-B.17 的决策边界

### 28.3 决策 2：最小可见层到底是哪一层

#### 方案 A：停在 `source_engine.py` 邻接 seam 的局部层

优点：

- 最保守
- 与当前仓库实现完全一致

缺点：

- 这仍然只是 3-B.16 的 internal signal carrying
- 不足以称为 runtime-visible gating

风险：

- 下一轮会继续重复“还在局部 helper 层”

#### 方案 B：允许进入更高层 internal decision boundary

优点：

- 能定义一个比 helper 局部层更高、但仍不对外可见的最小可见层
- 与 3-B.17 的“runtime-visible 但仍 internal-only”最一致
- 最利于下一轮实现 minimal runtime-visible gating skeleton

缺点：

- 需要严格限制这个 higher-layer boundary 仍不拥有 runtime error surface

风险：

- 如果 boundary 设计过宽，容易膨胀成新的 runtime decision owner

#### 方案 C：允许进入 public exception / public response surface 试探接近

优点：

- 最接近 future 对外行为

缺点：

- 当前缺少 public no-regression 证据
- 当前缺少 error surface 映射冻结

风险：

- 会直接把 3-B.17 写成 behavior 已开始生效

#### 推荐结论

推荐 **方案 B**。

当前阶段最安全的上限应固定为：

- future 一个更高层的 `internal decision boundary`

它可以：

- 读取 detector gate result
- 携带 internal surfaced signal 更久一点

但它当前仍然明确 **不是**：

- public response surface
- public exception surface
- runtime error surface owner

不推荐方案 A 的原因：

- 它还不够“runtime-visible”

不推荐方案 C 的原因：

- 当前证据不足以允许 public-layer 试探接近

### 28.4 决策 3：允许被 runtime-visible gating 感知的行为与绝对禁止的行为

#### 方案 A：只允许 internal carrying / observation

优点：

- 最稳
- 与当前 no-behavior-change 口径一致

缺点：

- 对下一轮 higher-layer skeleton 的指导不足

风险：

- 可能继续重复 3-B.16 的结论

#### 方案 B：允许 internal surfaced signal，但不改外部行为

优点：

- 更贴近 runtime-visible gating 的真实用途
- 能帮助 future higher-layer boundary 持有 detector classification 更久一点
- 仍然不会触碰 public behavior

缺点：

- 需要更明确的文档和测试规划去钉住禁止项

风险：

- 如果边界失控，会继续滑向 control-flow 变化

#### 方案 C：允许 detector result 开始影响控制流

优点：

- 推进快

缺点：

- 一旦影响控制流，就已经不是 runtime-visible gating，而是 runtime behavior change

风险：

- 会污染 parser / response_guard / API / error surface

#### 推荐结论

推荐 **方案 B**，但仍然只限 internal-only 范围。

future 最小 runtime-visible gating 后，允许的行为最多包括：

- internal higher-layer boundary 携带 detector gate signal
- internal decision boundary 读取 detector classification
- 为 future error-surface mapping 提供证据

此阶段绝对禁止的行为包括：

- API schema / API body 改变
- runtime exception surface 改变
- parser/content_parse 分支变化
- response_guard 被 detector 结果改写
- browser/js/fallback/retry 行为触发
- detector 结果直接控制业务流程

这些禁止项应继续通过两类方式钉住：

- 文档：明确写“runtime-visible gating != runtime-visible behavior”
- 测试规划：继续要求 no-behavior-change / no-surface-change / no-parser-branch-change

不推荐方案 A 的原因：

- 对下一轮 minimal runtime-visible skeleton 的指导不够

不推荐方案 C 的原因：

- 已经越界进入 runtime behavior 变化

### 28.5 决策 4：错误码何时可以真正接近 runtime surface

#### 方案 A：runtime-visible gating skeleton 一落地就允许部分 detector 错误码升级

优点：

- 口径简单

缺点：

- 与当前 `adapter_modeled` 口径冲突
- 会把 higher-layer internal carrying 误写成 runtime actually raises

风险：

- 最容易把 challenge/gateway 写成线上已支持

#### 方案 B：允许更高层 internal carrying，但仍不升级为 runtime-implemented

优点：

- 能承认 future higher-layer boundary 比 3-B.16 更进一步
- 同时保持错误码状态不越界

缺点：

- 需要把 higher-layer carrying 与错误码 lifecycle 明确拆开

风险：

- 如果表达不清，仍会引起误读

#### 方案 C：只有真正 runtime-visible behavior change 且可稳定复现后才升级

优点：

- 与当前文档体系和仓库事实最一致
- 最能防止阶段误导

缺点：

- 状态升级更保守

风险：

- 需要继续接受“错误码状态暂不升级”的约束

#### 推荐结论

推荐 **方案 C**，同时接受 **方案 B** 的概念层结论：

- future runtime-visible gating 可以允许更高层 internal carrying
- 但 challenge/gateway 错误码 lifecycle 仍然 **不因此升级**

也就是说：

- `recommended only`
- `internal observed`
- `internal carried`
- `internal surfaced near runtime`

这些都只能作为 future runtime-visible 行为语义，不应被写成新的错误码 lifecycle 状态。

因此 challenge/gateway 当前继续保持：

- `adapter_modeled`

只有同时满足以下条件后，才允许 future 真正接近 runtime surface：

1. 哪类 internal gate result 允许 first become runtime-visible 已被单独决策
2. runtime-visible gating 与 error surface / API / parser 的关系已冻结
3. public behavior 变化已被单独评估并可稳定复现
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

不推荐方案 A 的原因：

- 会直接破坏错误码状态体系

不推荐方案 B 的原因：

- 只可作为行为语义结论，不应被误写成 lifecycle 升级

### 28.6 决策 5：下一轮最小可执行任务是什么

#### 方案 A：继续只做 runtime-visible 文档设计

优点：

- 最保守

缺点：

- 当前 runtime-visible boundary 已足够清楚，继续纯文档会明显重复

风险：

- 推进停滞

#### 方案 B：进入 minimal runtime-visible gating skeleton 实现（仅更高层 internal carrying）

优点：

- 仍然不进入 runtime-visible behavior
- 能把 3-B.17 的边界结论收敛成最小 higher-layer internal boundary contract
- 最利于证明：
  - detector gate result 可以更高层可见
  - external behavior 仍零变化

缺点：

- 需要极严范围控制

风险：

- 如果把 higher-layer carrying 写成 public behavior 变化，就会越界

#### 方案 C：直接进入 detector 结果影响 runtime 的最小实装

优点：

- 推进快

缺点：

- 当前仍缺 error surface / API / parser 接缝冻结
- 当前仍缺 public no-regression 证据
- 当前仍缺哪些结果允许 first become runtime-visible 的正式证据链

风险：

- 会直接跨进 runtime-visible behavior change

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个更高层 internal runtime-visible gate boundary contract
- 一个 source-engine 邻接的 higher-layer carrying helper
- detector gate result 的 internal surfaced-near-runtime carrying
- 仍然不改返回值、不改异常、不改 parser、不改 response_guard
- 对应的 no-behavior-change / no-surface-change 测试

下一轮建议阶段名为：

- **Phase 3-B.18：detector runtime-visible minimal gating skeleton 实现**

当前不推荐直接进入 runtime-visible behavior change，原因是：

- 仍缺 runtime-visible boundary 与 external behavior 的明确映射
- 仍缺 public behavior change 的独立决策轮
- 仍缺 challenge/gateway visible behavior 的稳定验证

### 28.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前 minimal gating skeleton 已足够证明 detector result 到达 internal gate-layer
- 当前最危险的歧义是 runtime-visible 会不会被误写成 behavior 已生效
- 本轮已经足够决定下一轮能否安全进入 minimal runtime-visible gating skeleton

#### Step 2：如果主张本轮必须落代码，是否已有充分证明

结论：**没有**。

当前无法证明：

- 不落代码会阻塞 3-B.17
- 需要落的代码已小到不可再小
- 新增代码不会构成 runtime-visible behavior
- 新增代码不会影响既有链路

因此 3-B.17 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 runtime-visible gating skeleton 实装。

## 29. 3-B.18 detector runtime-visible minimal gating skeleton 实现结论

### 29.1 当前 minimal runtime-visible gating skeleton 最小落点

按 3-B.17 已冻结的边界，本轮 minimal runtime-visible gating skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_runtime_visible_gate.py`
- `backend/app/services/online/detector_runtime_visible_gating_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_runtime_visible_gate.py`
  - 只负责 higher-layer internal visible gate input / result / signal / noop decision contract
- `detector_runtime_visible_gating_skeleton.py`
  - 只负责 gate result -> visible gate input -> visible gate result 的最小 no-op helper
- `source_engine.py`
  - 只在现有 minimal gating no-op 调用之后再追加一层更高层 internal carrying
  - 调用结果继续停留在 internal-only 层

本轮没有把 runtime-visible gating 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 29.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorRuntimeVisibleGateInput`
- `DetectorRuntimeVisibleGateSignal`
- `DetectorRuntimeVisibleGateResult`
- `DetectorRuntimeVisibleGateOutcome`
- `DetectorRuntimeVisibleGateDecision`
- minimal runtime-visible gating helper
- source-engine 邻接更高层 runtime-visible no-op 调用点
- runtime-visible gating fixtures
- visible gate contract / helper / higher-layer carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_runtime_visible_gate.py`
- `backend/app/services/online/detector_runtime_visible_gating_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_runtime_visible_gating_samples.json`
- `backend/tests/test_online_detector_runtime_visible_gating_skeleton.py`

### 29.3 当前 runtime-visible gating skeleton 允许做到什么

本轮当前只允许做到：

- internal visible gate input 被构造
- internal visible gate result 被构造
- detector result 被内部携带到更高层 internal boundary
- visible gate helper 返回 no-op decision
- source-engine 邻接更高层位置内部调用 visible gating helper

其中 current higher-layer carrying 只表达：

- detector candidate 的 internal surfaced-near-runtime carrying
- 以及对应 recommended error code 仅作为 internal-only 信息

### 29.4 当前 runtime-visible gating skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime-visible gating 生效
- detector live runtime
- runtime error surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime-visible gating 生效
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 29.5 为什么这仍然不等于 runtime-visible gating 生效

因为本轮新增 visible gating 只做：

- higher-layer internal carrying
- no-op visible gate decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 visible gating helper 调用仍被内部 no-op guard 包裹：

- 即便 visible gating helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal runtime-visible gating skeleton implemented internally, runtime-visible behavior still unchanged

### 29.6 错误码状态结论

本轮没有新增 detector 错误码生命周期状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_observed`
- `internal_surfaced`
- `internal_carried`
- `internal_surfaced_near_runtime`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

### 29.7 下一步最小任务

在 3-B.18 之后，最小的下一步建议应是：

- **Phase 3-B.19：detector runtime error surface 决策轮**

该轮只应继续回答：

- 哪类 visible gate result future 有资格 first map to runtime error surface
- runtime error surface 与 API / parser / response_guard 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime-visible gating 生效
- runtime error surface 变化
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 30. 3-B.19 detector runtime error surface 决策轮结论

### 30.1 当前仓库还缺什么

在 3-B.18 之后，仓库已经能够稳定证明：

- detector result 可以经过：
  - `observe_live_entry_from_success_response(...)` / `observe_live_entry_from_fetch_error(...)`
  - `evaluate_detector_behavior_gate_noop(...)`
  - `evaluate_detector_runtime_visible_gate_noop(...)`
- 并最终到达：
  - `DetectorRuntimeVisibleGateResult.runtime_visible_signal`

但当前仓库仍然 **没有** 任何代码会把这些 internal 结果继续映射为：

- public exception
- public API error body / response shape
- `source_engine.py` 对外返回/抛错变化
- parser / content_parse / response_guard 的新分支

这说明当前最缺的不是 helper，而是对 `runtime error surface` 本身的严格边界定义。

### 30.2 决策 1：`runtime error surface` 的定义

#### 方案 A：只把 public exception / public API error body / 已实际改变控制流的 runtime-facing error category 视为 runtime error surface

优点：

- 术语最清晰
- 最不容易把 internal carrying 误写成 runtime 已生效
- 最符合当前仓库证据

缺点：

- 需要单独再定义一个“更靠近 surface 的 internal mapping boundary”

风险：

- 推进上看起来更保守

#### 方案 B：把更高层 internal mapping boundary 也算作广义 runtime error surface 邻接层

优点：

- 便于描述 future mapping 方向

缺点：

- 容易把 internal mapping boundary 和真正 surface 混在一起

风险：

- 后续 AI 容易把 “near surface” 直接写成 “already surfaced”

#### 方案 C：只要比 helper 更高层就都算 runtime error surface

优点：

- 叙述最省事

缺点：

- 基本失去边界意义

风险：

- 最容易造成阶段误导

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- `runtime error surface` 只指真正会影响对外异常类型、对外可见错误码、API error body/shape，或上层 service 已实际感知并改变控制流的 runtime-facing error category
- 以下内容都 **不属于** runtime error surface：
  - helper 局部变量
  - internal carried signal
  - `DetectorGateResult`
  - `DetectorRuntimeVisibleGateResult`
  - fixtures/sample 中的 recommended error code

不推荐方案 B 的原因：

- 会把 internal mapping boundary 和 true runtime surface 混在一起

不推荐方案 C 的原因：

- 会直接摧毁整个 3-B 分阶段语义

### 30.3 决策 2：detector result 最小允许接近的层级

#### 方案 A：继续停在 internal carried recommendation only

优点：

- 最保守

缺点：

- 与 3-B.18 的当前状态几乎重叠
- 下一轮推进空间过小

风险：

- 容易形成文档停滞

#### 方案 B：允许进入 internal surface-candidate mapping layer

优点：

- 能为 future runtime error surface skeleton 提供最小内部落点
- 仍然不触碰 public exception / API surface
- 与当前 3-B.18 higher-layer carrying 的结构连续

缺点：

- 需要额外强调“mapping boundary 不是 runtime surface”

风险：

- 如果文档口径不严格，可能被误读为 external behavior change

#### 方案 C：允许直接进入 public exception / public API error surface

优点：

- 推进最快

缺点：

- 直接越界进入 runtime-facing behavior change

风险：

- 会让 challenge/gateway 被误写成已对外生效

#### 推荐结论

推荐 **方案 B**。

本轮固定：

- detector result future 最多只允许 first approach：
  - 一个 internal-only `runtime error mapping boundary`
- 这个 boundary 最多只负责：
  - 消费 visible gate result
  - 产出 internal mapping candidate
- 它仍然 **不是**：
  - public exception owner
  - API error body owner
  - parser / response_guard owner
  - fallback / browser / JS owner

不推荐方案 A 的原因：

- 它已经不足以成为下一轮的最小有效推进点

不推荐方案 C 的原因：

- 它已经不再是 “mapping discussion”，而是 public behavior change

### 30.4 决策 3：哪些 detector result 可以进入 future error-surface 讨论

#### 方案 A：只允许 challenge / gateway 进入 first-batch discussion

优点：

- 与当前 detector first-batch sample / heuristic 现实一致
- 推荐错误码已存在且语义较稳定

缺点：

- 覆盖面保守

风险：

- 仍需谨防误写成 live support

#### 方案 B：再加入 suspicious HTML

优点：

- 讨论面更广

缺点：

- false positive 风险明显更高
- 与站点语义、内容解析语义耦合更强

风险：

- 很容易误伤正常 HTML

#### 方案 C：连 browser-required / js-required 也一起拉入

优点：

- 看起来更完整

缺点：

- 已明显越过当前 3-B 边界
- 会逼近 3-C / 3-D

风险：

- 直接制造阶段口径漂移

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- future runtime-facing mapping discussion first-batch 只允许：
  - challenge candidate
  - gateway candidate
- 它们当前最多只允许以以下形式存在：
  - recommended only
  - internal mapping candidate
  - future gated mapping candidate
- 以下内容当前继续排除在 runtime-facing mapping discussion 之外：
  - suspicious HTML
  - browser-required
  - js-required

不推荐方案 B 的原因：

- suspicious HTML 当前误判风险与站点语义依赖都明显更高

不推荐方案 C 的原因：

- browser/js-required 会把 3-B 讨论提前拖进 3-C / 3-D

### 30.5 决策 4：错误码何时才有资格进入 runtime-facing 映射讨论

#### 方案 A：只要已有 runtime-visible higher-layer carrying 就可进入 mapping skeleton

优点：

- 推进快

缺点：

- 证据远远不够

风险：

- 容易把 3-B.18 误写成 “almost runtime implemented”

#### 方案 B：必须 additional evidence 齐全后才允许进入

优点：

- 与当前仓库最一致
- 能把 internal carrying 和 future runtime-facing mapping gate 明确区分

缺点：

- 进入下一轮前需要继续保持保守口径

风险：

- 推进速度看起来较慢

#### 方案 C：等完整 detector live runtime 再讨论

优点：

- 最稳

缺点：

- 过度保守
- 会让最小 internal mapping skeleton 无法顺序推进

风险：

- 把本可拆开的边界问题再次捆在一起

#### 推荐结论

推荐 **方案 B**。

本轮固定：`LEGADO_ANTI_BOT_CHALLENGE` 与 `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 若 future 要进入 runtime-facing mapping skeleton 讨论，仍至少需要满足：

1. 3-B.18 的 runtime-visible higher-layer carrying 已稳定存在，且 no-op 语义清晰
2. positive / negative / no-regression 证据继续存在并覆盖 success / error path
3. future internal mapping contract 的 owner、输入、输出都已冻结
4. public behavior change 尚未发生，但“为什么这仍不是 public behavior”已能被文档和测试清楚证明
5. parser / response_guard / API / exception surface 继续与 detector mapping boundary 隔离

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都仍然只能保持：

- `adapter_modeled`

不推荐方案 A 的原因：

- 仅凭 visible carrying 还不足以支撑 runtime-facing 讨论

不推荐方案 C 的原因：

- 会把 “internal mapping boundary” 这一步完全抹掉

### 30.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 mapping 文档设计

优点：

- 最保守

缺点：

- 3-B.19 已经把最关键的 runtime surface boundary 固定完了
- 再纯文档一轮会明显重复

风险：

- 推进停滞

#### 方案 B：进入 minimal runtime error surface skeleton 实现（仅 internal mapping contract / no-op mapping）

优点：

- 与当前仓库证据链最连续
- 仍然可以严格保持 no-behavior-change
- 有利于验证 internal mapping boundary 的最小可回退结构

缺点：

- 需要非常严格的命名和测试保护

风险：

- 若口径失守，会被误写成 detector error 已可对外抛出

#### 方案 C：直接进入 detector 错误码最小 runtime-facing 实装

优点：

- 推进最快

缺点：

- 已经直接进入 runtime-facing behavior change

风险：

- 极易造成 public exception / API surface 污染

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 internal-only runtime error mapping input/result contract
- 一个 visible gate result -> internal mapping candidate 的 no-op helper
- 一个 `source_engine.py` 邻接的 internal mapping 调用点
- 对应的 no-behavior-change / no-exception-surface-change / no-api-surface-change 测试

下一轮仍然 **不允许** 进入：

- public exception change
- public API error shape change
- challenge/gateway 对外抛错
- parser / response_guard 联动
- anti-bot bypass
- browser / JS fallback

### 30.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前仓库已经有足够证据证明 detector result 最多到达 `runtime_visible_signal`
- 当前最危险的歧义不在 helper 缺失，而在 runtime surface 术语边界
- 3-B.19 已足够为下一轮最小 internal mapping skeleton 收敛边界

#### Step 2：如果主张本轮必须落代码，是否已经有充分证明

结论：**没有**。

当前仍无法证明：

- 不落代码会阻塞 3-B.19 结论形成
- 本轮存在一个最小不可再小、且不被误写成 runtime-facing behavior 的代码集合
- 本轮代码不会污染 `source_engine.py` 的对外异常/返回语义

因此 3-B.19 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 runtime error surface skeleton 实装。

## 31. 3-B.20 detector runtime error surface minimal skeleton 实现结论

### 31.1 当前 minimal runtime error surface skeleton 的最小落点

按 3-B.19 已冻结的边界，本轮 minimal runtime error surface skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_runtime_error_mapping.py`
- `backend/app/services/online/detector_runtime_error_mapping_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_runtime_error_mapping.py`
  - 只负责 internal mapping input / candidate / result / noop decision contract
- `detector_runtime_error_mapping_skeleton.py`
  - 只负责 visible gate result -> mapping input -> mapping result 的最小 no-op helper
- `source_engine.py`
  - 只在现有 runtime-visible gating no-op 调用之后再追加一层更高层 internal mapping carrying
  - 调用结果继续停留在 internal-only 层

本轮没有把 runtime error mapping 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 31.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorRuntimeErrorMappingInput`
- `DetectorRuntimeErrorMappingCandidateKind`
- `DetectorRuntimeErrorMappingCandidate`
- `DetectorRuntimeErrorMappingResult`
- `DetectorRuntimeErrorMappingOutcome`
- `DetectorRuntimeErrorMappingDecision`
- minimal runtime error mapping helper
- source-engine 邻接更高层 runtime error mapping no-op 调用点
- runtime error mapping fixtures
- mapping contract / helper / higher-layer candidate carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_runtime_error_mapping.py`
- `backend/app/services/online/detector_runtime_error_mapping_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_runtime_error_mapping_samples.json`
- `backend/tests/test_online_detector_runtime_error_mapping_skeleton.py`

### 31.3 当前 runtime error mapping skeleton 允许做到什么

本轮当前只允许做到：

- internal mapping input 被构造
- internal mapping result 被构造
- detector result 被内部携带到一个更靠近 runtime error surface 的 internal mapping boundary
- mapping helper 返回 no-op decision
- source-engine 邻接更高层位置内部调用 runtime error mapping helper

其中 current higher-layer mapping carrying 只表达：

- challenge / gateway detector candidate 的 internal mapping candidate carrying
- 对应 recommended error code 仅作为 internal-only 信息
- 当前 helper 已经可以区分：
  - `no_mapping_candidate`
  - `mapping_candidate_carried`

### 31.4 当前 runtime error mapping skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime error surface 生效
- detector live runtime
- public exception surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime error surface 生效
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 31.5 为什么这仍然不等于 runtime error surface 生效

因为本轮新增 runtime error mapping 只做：

- internal mapping candidate carrying
- no-op mapping decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 runtime error mapping helper 调用仍被内部 no-op guard 包裹：

- 即便 mapping helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal runtime error surface skeleton implemented internally, runtime error surface behavior still unchanged

### 31.6 错误码状态结论

本轮没有新增 detector 错误码 lifecycle 状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_mapped`
- `surface_candidate_carried`
- `runtime-facing_candidate`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

原因是：

- 当前 internal mapping skeleton 只证明“candidate 被更高层 internal boundary 看见了”
- 并没有证明 detector 错误码已经会对外抛出

### 31.7 下一步最小任务

在 3-B.20 之后，最小的下一步建议应是：

- **Phase 3-B.21：detector runtime-facing error gate 决策轮**

该轮只应继续回答：

- 哪类 internal mapping candidate future 有资格 first approach runtime-facing error gate
- runtime-facing error gate 与 public exception / API / parser / response_guard 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime error surface 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 32. 3-B.21 detector runtime-facing error gate 决策轮结论

### 32.1 当前仓库还缺什么

在 3-B.20 之后，仓库已经能够稳定证明：

- detector result 可以经过：
  - live-entry observation
  - minimal gating carrying
  - runtime-visible carrying
  - runtime error mapping candidate carrying
- 并最终到达：
  - `DetectorRuntimeErrorMappingResult.mapping_candidate`

但当前仓库仍然 **没有** 任何代码会把这些 internal 结果继续送入：

- 某个“最后 internal gate owner”
- public exception owner
- public API error body / shape owner
- 任何会改变 `source_engine.py` return / raise 的 runtime-facing decision

这说明当前最缺的不是新的 helper，而是对 `runtime-facing error gate` 本身的术语、层级和候选范围做最后一次严格冻结。

### 32.2 决策 1：`runtime-facing error gate` 的定义

#### 方案 A：仅 public exception / public API error body 前的最后 internal gate 属于 runtime-facing error gate

优点：

- 术语最清晰
- 最不容易把 internal mapping candidate 误写成 runtime 已生效
- 最符合当前仓库分层

缺点：

- 需要额外说明“哪些 internal result 仍只是邻接层，不是 gate 本身”

风险：

- 推进上看起来更保守

#### 方案 B：更高层 internal mapping boundary 也算广义 runtime-facing gate 邻接层

优点：

- 便于描述 future 过渡关系

缺点：

- 容易把 mapping boundary 和真正 gate 混在一起

风险：

- 后续 AI 容易把 “near gate” 直接写成 “already runtime-facing”

#### 方案 C：只要比 helper 更高层都算 runtime-facing gate

优点：

- 叙述最省事

缺点：

- 几乎失去边界意义

风险：

- 阶段口径最容易崩掉

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- `runtime-facing error gate` 只指：
  - public exception / public API error surface 之前的最后一个 internal gate
  - 某个 future internal owner deciding whether detector candidate may approach external error behavior
  - runtime-facing mapping decision 之前的最后 internal boundary
- 以下内容都 **不属于** runtime-facing error gate：
  - helper 局部变量
  - internal carried signal
  - `DetectorRuntimeVisibleGateResult`
  - `DetectorRuntimeErrorMappingResult`
  - tests / fixtures 中的 recommended error code

不推荐方案 B 的原因：

- 会把邻接层和 gate 本体混在一起

不推荐方案 C 的原因：

- 会直接摧毁整个 3-B 的阶段术语体系

### 32.3 决策 2：detector result / mapping candidate 最小允许接近的层级

#### 方案 A：继续停在 internal mapping candidate

优点：

- 最保守

缺点：

- 与 3-B.20 当前状态几乎重叠
- 下一轮推进空间过小

风险：

- 容易形成文档停滞

#### 方案 B：允许进入 internal runtime-facing gate boundary

优点：

- 能为 future runtime-facing error gate skeleton 提供最小内部落点
- 仍然不触碰 public exception / API surface
- 与当前 3-B.20 mapping candidate 结构连续

缺点：

- 需要额外强调“gate boundary 不是 runtime-facing behavior”

风险：

- 若文档口径不严，可能被误读为 external behavior change

#### 方案 C：允许进入 public exception / public response surface 试探接近

优点：

- 推进最快

缺点：

- 直接越界进入 runtime-facing behavior change

风险：

- 会让 challenge/gateway 被误写成已对外生效

#### 推荐结论

推荐 **方案 B**。

本轮固定：

- detector result / mapping candidate future 最多只允许 first approach：
  - 一个 internal-only `runtime-facing error gate boundary`
- 这个 boundary 最多只负责：
  - 消费 internal mapping candidate
  - 产出 internal gate candidate / no-op gate decision
- 它仍然 **不是**：
  - public exception owner
  - API error body owner
  - parser / response_guard owner
  - fallback / browser / JS owner

不推荐方案 A 的原因：

- 它已经不足以成为下一轮的最小有效推进点

不推荐方案 C 的原因：

- 它已经不再是 gate discussion，而是 public behavior change

### 32.4 决策 3：哪些 candidate 可以进入 future runtime-facing gate 讨论

#### 方案 A：只允许 challenge / gateway 进入 first-batch discussion

优点：

- 与当前 detector first-batch sample / heuristic / mapping candidate 现实一致
- 推荐错误码已存在且语义相对稳定

缺点：

- 覆盖面保守

风险：

- 仍需谨防误写成 live support

#### 方案 B：再加 suspicious HTML

优点：

- 讨论面更广

缺点：

- false positive 风险更高
- 与站点语义、内容解析语义耦合更强

风险：

- 很容易误伤正常 HTML

#### 方案 C：再把 browser-required / js-required 也拉进来

优点：

- 看起来更完整

缺点：

- 已明显越过当前 3-B 边界
- 会逼近 3-C / 3-D

风险：

- 直接制造阶段口径漂移

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- future runtime-facing gate discussion first-batch 只允许：
  - challenge candidate
  - gateway candidate
- 它们当前最多只允许以以下形式存在：
  - recommended only
  - internal mapping candidate
  - internal runtime-facing gate candidate
- 以下内容当前继续排除在 runtime-facing gate discussion 之外：
  - suspicious HTML
  - browser-required
  - js-required

不推荐方案 B 的原因：

- suspicious HTML 当前误判风险与站点语义依赖都明显更高

不推荐方案 C 的原因：

- browser/js-required 会把 3-B 讨论提前拖进 3-C / 3-D

### 32.5 决策 4：错误码何时才有资格进入 runtime-facing gate 讨论

#### 方案 A：只要已有 runtime error mapping candidate 就可进入 gate skeleton

优点：

- 推进快

缺点：

- 证据远远不够

风险：

- 容易把 3-B.20 误写成 almost runtime implemented

#### 方案 B：必须 additional evidence 齐全后才允许进入

优点：

- 与当前仓库最一致
- 能把 internal mapping candidate 和 future runtime-facing gate 明确区分

缺点：

- 进入下一轮前需要继续保持保守口径

风险：

- 推进速度看起来较慢

#### 方案 C：等完整 detector live runtime 再讨论

优点：

- 最稳

缺点：

- 过度保守
- 会让最小 internal gate skeleton 无法顺序推进

风险：

- 把本可拆开的边界问题再次捆在一起

#### 推荐结论

推荐 **方案 B**。

本轮固定：`LEGADO_ANTI_BOT_CHALLENGE` 与 `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 若 future 要进入 runtime-facing gate skeleton 讨论，仍至少需要满足：

1. 3-B.20 的 higher-layer internal mapping candidate carrying 已稳定存在，且 no-op 语义清晰
2. positive / negative / no-regression 证据继续存在并覆盖 success / error path
3. future internal runtime-facing gate contract 的 owner、输入、输出都已冻结
4. public behavior change 尚未发生，但“为什么这仍不是 public behavior”已能被文档和测试清楚证明
5. parser / response_guard / API / exception surface 继续与 detector gate boundary 隔离

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都仍然只能保持：

- `adapter_modeled`

不推荐方案 A 的原因：

- 仅凭 mapping candidate 还不足以支撑 runtime-facing gate 讨论

不推荐方案 C 的原因：

- 会把 “internal runtime-facing gate boundary” 这一步完全抹掉

### 32.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 runtime-facing gate 文档设计

优点：

- 最保守

缺点：

- 3-B.21 已经把最关键的 gate boundary 固定完了
- 再纯文档一轮会明显重复

风险：

- 推进停滞

#### 方案 B：进入 minimal runtime-facing error gate skeleton 实现（仅 internal gate contract / no-op gate）

优点：

- 与当前仓库证据链最连续
- 仍然可以严格保持 no-behavior-change
- 有利于验证 internal gate boundary 的最小可回退结构

缺点：

- 需要非常严格的命名和测试保护

风险：

- 若口径失守，会被误写成 detector error 已可对外抛出

#### 方案 C：直接进入 detector 错误码最小 runtime-facing 生效实装

优点：

- 推进最快

缺点：

- 已经直接进入 runtime-facing behavior change

风险：

- 极易造成 public exception / API surface 污染

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 internal-only runtime-facing gate input/result contract
- 一个 mapping candidate -> internal gate candidate 的 no-op helper
- 一个 `source_engine.py` 邻接的 internal gate 调用点
- 对应的 no-behavior-change / no-exception-surface-change / no-api-surface-change 测试

下一轮仍然 **不允许** 进入：

- public exception change
- public API error shape change
- challenge/gateway 对外抛错
- parser / response_guard 联动
- anti-bot bypass
- browser / JS fallback

### 32.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前仓库已经有足够证据证明 detector result 最多到达 `mapping_candidate`
- 当前最危险的歧义不在 helper 缺失，而在 runtime-facing gate 术语边界
- 3-B.21 已足够为下一轮最小 internal gate skeleton 收敛边界

#### Step 2：如果主张本轮必须落代码，是否已经有充分证明

结论：**没有**。

当前仍无法证明：

- 不落代码会阻塞 3-B.21 结论形成
- 本轮存在一个最小不可再小、且不被误写成 runtime-facing behavior 的代码集合
- 本轮代码不会污染 `source_engine.py` 的对外异常/返回语义

因此 3-B.21 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 runtime-facing error gate skeleton 实装。

## 33. 3-B.22 detector runtime-facing error gate minimal skeleton 实现结论

### 33.1 当前 minimal runtime-facing error gate skeleton 的最小落点

按 3-B.21 已冻结的边界，本轮 minimal runtime-facing error gate skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_runtime_facing_gate.py`
- `backend/app/services/online/detector_runtime_facing_gate_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_runtime_facing_gate.py`
  - 只负责 internal gate input / candidate / result / noop decision contract
- `detector_runtime_facing_gate_skeleton.py`
  - 只负责 mapping candidate -> gate input -> gate result 的最小 no-op helper
- `source_engine.py`
  - 只在现有 runtime error mapping no-op 调用之后再追加一层更高层 internal gate carrying
  - 调用结果继续停留在 internal-only 层

本轮没有把 runtime-facing gate 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 33.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorRuntimeFacingGateInput`
- `DetectorRuntimeFacingGateCandidateKind`
- `DetectorRuntimeFacingGateCandidate`
- `DetectorRuntimeFacingGateResult`
- `DetectorRuntimeFacingGateOutcome`
- `DetectorRuntimeFacingGateDecision`
- minimal runtime-facing gate helper
- source-engine 邻接更高层 runtime-facing gate no-op 调用点
- runtime-facing gate fixtures
- gate contract / helper / higher-layer gate candidate carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_runtime_facing_gate.py`
- `backend/app/services/online/detector_runtime_facing_gate_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_runtime_facing_gate_samples.json`
- `backend/tests/test_online_detector_runtime_facing_gate_skeleton.py`

### 33.3 当前 runtime-facing gate skeleton 允许做到什么

本轮当前只允许做到：

- internal gate input 被构造
- internal gate result 被构造
- detector result 被内部携带到一个更靠近 runtime-facing error gate 的 internal boundary
- gate helper 返回 no-op decision
- source-engine 邻接更高层位置内部调用 runtime-facing gate helper

其中 current higher-layer gate carrying 只表达：

- challenge / gateway detector candidate 的 internal gate candidate carrying
- 对应 recommended error code 仅作为 internal-only 信息
- 当前 helper 已经可以区分：
  - `no_gate_candidate`
  - `gate_candidate_carried`

### 33.4 当前 runtime-facing gate skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime-facing error gate 生效
- detector live runtime
- public exception surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime-facing error gate 生效
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 33.5 为什么这仍然不等于 runtime-facing error gate 生效

因为本轮新增 runtime-facing gate 只做：

- internal gate candidate carrying
- no-op gate decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 runtime-facing gate helper 调用仍被内部 no-op guard 包裹：

- 即便 gate helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal runtime-facing error gate skeleton implemented internally, runtime-facing error gate behavior still unchanged

### 33.6 错误码状态结论

本轮没有新增 detector 错误码 lifecycle 状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_gate_candidate`
- `runtime-facing_candidate`
- `external_gate_ready`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

原因是：

- 当前 runtime-facing gate skeleton 只证明“candidate 被更高层 internal gate boundary 看见了”
- 并没有证明 detector 错误码已经会对外抛出

### 33.7 下一步最小任务

在 3-B.22 之后，最小的下一步建议应是：

- **Phase 3-B.23：detector runtime-facing behavior gate 决策轮**

该轮只应继续回答：

- 哪类 internal gate candidate future 有资格 first approach runtime-facing behavior gate
- runtime-facing behavior gate 与 public exception / API / parser / response_guard 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime-facing error gate 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 34. 3-B.23 detector runtime-facing behavior gate 决策轮结论

### 34.1 当前 future runtime-facing behavior gate 还缺什么

按当前仓库证据，detector 结果已经可以沿着以下 internal-only 路径被更高层看到：

- `observe_live_entry_from_success_response` / `observe_live_entry_from_fetch_error`
- `evaluate_detector_behavior_gate_noop`
- `evaluate_detector_runtime_visible_gate_noop`
- `evaluate_detector_runtime_error_mapping_noop`
- `evaluate_detector_runtime_facing_gate_noop`

并且当前最高只到达：

- `DetectorRuntimeFacingGateResult.gate_candidate`
- `DetectorRuntimeFacingGateResult.gate_decision`

但这些结果仍然被 `source_engine.py` 中的 `_observe_live_entry_success_noop` / `_observe_live_entry_error_noop` 直接丢弃。当前仓库仍然没有任何代码让 detector 结果去影响：

- `fetch_service.py` 返回值
- `response_guard_service.py` 分类结果
- parser / `content_parse_service.py`
- public exception surface
- public API response shape
- runtime control flow

这说明当前最缺的不是新的 public-facing runtime 结构，而是：

- `runtime-facing behavior gate` 的严格定义
- detector result future 最多只允许接近到哪一层 internal boundary
- 哪些 detector candidate 有资格进入 future behavior-gate 讨论
- 候选错误码何时才有资格从“更靠近 behavior”进入真正的 behavior-gate skeleton 讨论

### 34.2 决策 1：`runtime-facing behavior gate` 的定义

#### 方案 A：仅 public exception / public API error / public control-flow change 前的最后 internal gate 属于 runtime-facing behavior gate

优点：

- 术语最清晰
- 最不容易把 internal carrying 误写成 external behavior
- 与当前 `runtime error surface`、`runtime-facing error gate` 的分层最一致

缺点：

- 需要额外说明哪些层只是邻接层而不是 gate 本体

风险：

- 推进显得更保守

#### 方案 B：更高层 internal mapping/gate boundary 也算广义 runtime-facing behavior gate 邻接层

优点：

- 便于描述 future 过渡层

缺点：

- 容易把邻接层与 gate 本体混写

风险：

- 后续 AI 容易把 “near behavior” 写成 “behavior already changed”

#### 方案 C：只要比 helper 更高层都算 runtime-facing behavior gate

优点：

- 叙述最省事

缺点：

- 几乎失去术语约束力

风险：

- 阶段口径最容易漂移

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- `runtime-facing behavior gate` 只指 public exception / public API error / public control-flow change 之前的最后一个 internal gate
- 它只表示 future 某个 internal owner deciding whether detector candidate may influence runtime behavior
- 它是 runtime-facing behavior change 之前的最后 internal boundary

以下内容都 **不属于** runtime-facing behavior gate：

- helper 局部变量
- internal carried signal
- visible gate result
- mapping candidate
- runtime-facing error gate result
- tests / fixtures 中的 recommended error code

其中：

- `runtime-facing error gate`
  - 仍然只是更靠近 external error surface 的最后 internal gate
- `runtime-facing behavior gate`
  - 则是更靠近 external behavior change 的最后 internal gate

两者都不等于 public behavior owner 本身。

不推荐方案 B 的原因：

- 会把 “邻接层” 和 “gate 本体” 混成一个术语

不推荐方案 C 的原因：

- 会直接摧毁当前 3-B 的分层精度

### 34.3 决策 2：detector result / gate candidate 最小允许接近的层级

#### 方案 A：仍停在 internal runtime-facing error gate candidate

优点：

- 最保守

缺点：

- 会把 3-B.22 之后的推进完全停在原地

风险：

- 文档收敛不足以支撑下一轮最小 skeleton

#### 方案 B：进入 internal runtime-facing behavior gate boundary

优点：

- 能形成下一轮最小 skeleton 的清晰上限
- 仍然不触碰 public exception / API / control flow
- 与当前 `runtime-facing gate candidate` 的更高层 internal carrying 连续

缺点：

- 需要持续强调 “接近 behavior” 不等于 “behavior 生效”

风险：

- 如果文档失守，容易被误读成 external behavior 已开始变化

#### 方案 C：进入 public exception / public response / public behavior surface 试探接近

优点：

- 推进最快

缺点：

- 已经不再是 gate discussion，而是 runtime-facing behavior change

风险：

- 会直接污染 public behavior 语义

#### 推荐结论

推荐 **方案 B**。

本轮固定：

- detector result / gate candidate future 最多只允许 first approach：
  - 一个 **internal-only runtime-facing behavior gate boundary**
- 这一层最多只负责：
  - 消费 internal runtime-facing error gate candidate
  - 产出 internal behavior-gate candidate / no-op behavior-gate decision
- 它仍然 **不是**：
  - public exception owner
  - public API owner
  - parser / response_guard owner
  - control-flow owner
  - fallback / browser / JS owner

这也说明：

- “接近 runtime-facing behavior gate”
  - 只表示 future internal carrying 可以更靠近 behavior 变化前的最后 gate
- 它仍然不等于：
  - public behavior change 已发生
  - challenge/gateway 已会影响线上返回或抛错

不推荐方案 A 的原因：

- 它已经不足以支撑下一轮最小、可回退的内部结构推进

不推荐方案 C 的原因：

- 它已经直接越过 3-B.23 的决策边界

### 34.4 决策 3：哪些 detector candidate 可以进入 future runtime-facing behavior gate 讨论

#### 方案 A：只允许 challenge / gateway 进入 first-batch 讨论

优点：

- 与当前 detector first-batch sample、mapping candidate、runtime-facing gate candidate 完全一致
- 语义相对收敛

缺点：

- 范围较窄

风险：

- 仍需持续防止被误写成 live support

#### 方案 B：再加 suspicious HTML

优点：

- 讨论覆盖面更广

缺点：

- 与 parser / stage / site semantics 耦合更强

风险：

- false positive 风险明显更高

#### 方案 C：再把 browser-required / js-required 也拉进来

优点：

- 看起来更完整

缺点：

- 已经把 3-B 讨论提前拖进 3-C / 3-D

风险：

- 阶段边界最容易失真

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- future runtime-facing behavior gate discussion first-batch 只允许：
  - challenge
  - gateway
- 它们当前最多只允许以以下形式存在：
  - recommended only
  - internal mapping candidate
  - internal runtime-facing error gate candidate
  - internal runtime-facing behavior gate candidate

以下内容当前继续排除在 discussion 之外：

- suspicious HTML
- browser-required
- js-required

原因是：

- suspicious HTML 仍然存在明显的误判风险与站点语义依赖
- browser/js-required 已经属于 future 3-C / 3-D 的讨论范围

不推荐方案 B 的原因：

- suspicious HTML 当前不足以稳定进入 behavior-gate 讨论

不推荐方案 C 的原因：

- browser/js-required 会直接把 3-B.23 讨论拖出当前阶段

### 34.5 决策 4：错误码何时才有资格进入 runtime-facing behavior 讨论

#### 方案 A：只要有 runtime-facing error gate candidate 就可进入 behavior gate skeleton

优点：

- 推进快

缺点：

- 当前证据明显不够

风险：

- 最容易把 3-B.22 误写成 almost runtime-implemented

#### 方案 B：必须 additional evidence 齐全后才进入

优点：

- 与当前仓库事实最一致
- 能把 “internal carrying” 与 “future behavior gate skeleton” 明确切开

缺点：

- 推进口径更保守

风险：

- 需要持续维护样本、回归与 no-regression 证据

#### 方案 C：等完整 detector live runtime 再讨论

优点：

- 最稳

缺点：

- 过度保守
- 会让最小 internal behavior-gate skeleton 无法顺序推进

风险：

- 把本可前置冻结的边界继续拖后

#### 推荐结论

推荐 **方案 B**。

本轮固定：`LEGADO_ANTI_BOT_CHALLENGE` 与 `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 若 future 要进入真正的 runtime-facing behavior gate skeleton 讨论，至少还需要满足：

1. higher-layer carrying 已稳定存在，且 no-op 语义清晰
2. internal mapping candidate 已稳定存在
3. internal runtime-facing error gate candidate 已稳定存在
4. 正样本、负样本与 no-regression 回归矩阵已具备
5. challenge/gateway 的误判风险已有进一步收敛证据
6. behavior-gate layer 的 owner、输入、输出与职责边界已冻结
7. public behavior change 尚未发生，但内部证据已经足够证明：
   - future behavior gate boundary 仍然不是 public behavior owner
   - future behavior gate boundary 仍然不会污染 parser / response_guard / API / exception surface

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

并且本轮不新增新的错误码 lifecycle 状态。

不推荐方案 A 的原因：

- 仅凭 runtime-facing error gate candidate 还不足以进入 behavior-gate skeleton 讨论

不推荐方案 C 的原因：

- 会把本可前置冻结的 behavior-gate 边界完全后移

### 34.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 runtime-facing behavior gate 文档设计

优点：

- 最保守

缺点：

- 3-B.23 已经把 behavior-gate 术语、上限和门槛冻结完了

风险：

- 再纯文档一轮会明显重复

#### 方案 B：进入 minimal runtime-facing behavior gate skeleton 实现（仅 internal gate contract / no-op gate）

优点：

- 与当前仓库证据链最连续
- 仍可保持 strict no-behavior-change
- 能验证 future behavior-gate boundary 的最小可回退结构

缺点：

- 需要更严格的命名、注释和 no-regression 测试

风险：

- 若口径失守，容易被误写成 “detector 结果已开始影响行为”

#### 方案 C：直接进入 detector 结果最小 runtime-facing behavior 生效实装

优点：

- 推进最快

缺点：

- 已经直接进入 runtime-facing behavior change

风险：

- 极易污染 public exception / API / parser / response_guard / control flow

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 internal-only runtime-facing behavior gate input / candidate / result / noop decision contract
- 一个 runtime-facing error gate candidate -> runtime-facing behavior gate candidate 的 no-op helper
- 一个 `source_engine.py` 邻接的 internal behavior-gate 调用点
- 对应的 no-behavior-change / no-exception-surface-change / no-api-surface-change / no-control-flow-change 测试

下一轮仍然 **不允许** 进入：

- detector live runtime 生效
- runtime-facing behavior gate 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- parser / response_guard 联动
- anti-bot bypass
- browser / JS fallback

### 34.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前仓库已经有足够证据证明 detector 结果最高只到 `runtime-facing gate candidate / no-op gate decision`
- 当前最危险的歧义已经不在 helper 缺失，而在 behavior-gate 术语与 public behavior 之间的边界
- 3-B.23 的目标就是把这条边界钉死，而不是继续增加 internal runtime 结构

#### Step 2：如果主张本轮必须落代码，是否已经有充分证明

结论：**没有**。

当前仍无法证明：

- 不落代码会阻塞下一轮
- 本轮存在一个最小不可再小、且不会被误写成 runtime-facing behavior change 的代码集合
- 本轮代码不会污染 `source_engine.py` 的对外返回/异常语义

因此 3-B.23 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 runtime-facing behavior gate skeleton 实装。

## 35. 3-B.24 detector runtime-facing behavior gate minimal skeleton 实现结论

### 35.1 当前 minimal runtime-facing behavior gate skeleton 的最小落点

按 3-B.23 已冻结的边界，本轮 minimal runtime-facing behavior gate skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_runtime_facing_behavior_gate.py`
- `backend/app/services/online/detector_runtime_facing_behavior_gate_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_runtime_facing_behavior_gate.py`
  - 只负责 internal behavior gate input / candidate / result / noop decision contract
- `detector_runtime_facing_behavior_gate_skeleton.py`
  - 只负责 runtime-facing error gate candidate -> behavior gate input -> behavior gate result 的最小 no-op helper
- `source_engine.py`
  - 只在现有 runtime-facing error gate no-op 调用之后再追加一层更高层 internal behavior gate carrying
  - 调用结果继续停留在 internal-only 层

本轮没有把 runtime-facing behavior gate 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 35.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorRuntimeFacingBehaviorGateInput`
- `DetectorRuntimeFacingBehaviorGateCandidateKind`
- `DetectorRuntimeFacingBehaviorGateCandidate`
- `DetectorRuntimeFacingBehaviorGateResult`
- `DetectorRuntimeFacingBehaviorGateOutcome`
- `DetectorRuntimeFacingBehaviorGateDecision`
- minimal runtime-facing behavior gate helper
- source-engine 邻接更高层 runtime-facing behavior gate no-op 调用点
- runtime-facing behavior gate fixtures
- behavior gate contract / helper / higher-layer behavior gate candidate carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_runtime_facing_behavior_gate.py`
- `backend/app/services/online/detector_runtime_facing_behavior_gate_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_runtime_facing_behavior_gate_samples.json`
- `backend/tests/test_online_detector_runtime_facing_behavior_gate_skeleton.py`

### 35.3 当前 runtime-facing behavior gate skeleton 允许做到什么

本轮当前只允许做到：

- internal behavior gate input 被构造
- internal behavior gate result 被构造
- detector result 被内部携带到一个更靠近 runtime-facing behavior gate 的 internal boundary
- behavior gate helper 返回 no-op decision
- source-engine 邻接更高层位置内部调用 runtime-facing behavior gate helper

其中 current higher-layer behavior gate carrying 只表达：

- challenge / gateway detector candidate 的 internal behavior gate candidate carrying
- 对应 recommended error code 仅作为 internal-only 信息
- 当前 helper 已经可以区分：
  - `no_behavior_gate_candidate`
  - `behavior_gate_candidate_carried`

### 35.4 当前 runtime-facing behavior gate skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime-facing behavior gate 生效
- detector live runtime
- public exception surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback / browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime-facing behavior gate 生效
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 35.5 为什么这仍然不等于 runtime-facing behavior gate 生效

因为本轮新增 runtime-facing behavior gate 只做：

- internal behavior gate candidate carrying
- no-op behavior gate decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- 改 API error body / response shape
- 改 control flow
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 runtime-facing behavior gate helper 调用仍被内部 no-op guard 包裹：

- 即便 behavior gate helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal runtime-facing behavior gate skeleton implemented internally, runtime-facing behavior gate behavior still unchanged

### 35.6 错误码状态结论

本轮没有新增 detector 错误码 lifecycle 状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_behavior_candidate`
- `behavior_gate_ready`
- `external_behavior_ready`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

原因是：

- 当前 runtime-facing behavior gate skeleton 只证明“candidate 被更高层 internal behavior gate boundary 看见了”
- 并没有证明 detector 错误码已经会对外抛出
- 更没有证明 runtime behavior 已经被改变

### 35.7 下一步最小任务

在 3-B.24 之后，最小的下一步建议应是：

- **Phase 3-B.25：detector runtime-facing behavior activation 决策轮**

该轮只应继续回答：

- 哪类 internal behavior gate candidate future 有资格进入真正的 runtime-facing behavior activation 讨论
- runtime-facing behavior gate 与 public exception / API / parser / response_guard / control-flow 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime-facing behavior gate 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass

## 36. 3-B.25 detector runtime-facing behavior activation 决策轮结论

### 36.1 当前 future runtime-facing behavior activation 还缺什么

按当前仓库证据，detector 结果已经可以沿着以下 internal-only 路径被更高层看到：

- `observe_live_entry_from_success_response` / `observe_live_entry_from_fetch_error`
- `evaluate_detector_behavior_gate_noop`
- `evaluate_detector_runtime_visible_gate_noop`
- `evaluate_detector_runtime_error_mapping_noop`
- `evaluate_detector_runtime_facing_gate_noop`
- `evaluate_detector_runtime_facing_behavior_gate_noop`

并且当前最高只到达：

- `DetectorRuntimeFacingBehaviorGateResult.behavior_gate_candidate`
- `DetectorRuntimeFacingBehaviorGateResult.behavior_gate_decision`

但这些结果仍然被 `source_engine.py` 中的 `_observe_live_entry_success_noop` / `_observe_live_entry_error_noop` 直接丢弃。当前仓库仍然没有任何代码让 detector 结果去影响：

- `fetch_service.py` 返回值
- `response_guard_service.py` 分类结果
- parser / `content_parse_service.py`
- public exception surface
- public API response shape
- runtime control flow
- fallback / browser / js dispatch

这说明当前最缺的不是新的 public-facing runtime 结构，而是：

- `runtime-facing behavior activation` 的严格定义
- detector result future 最多只允许接近到哪一层 internal activation boundary
- 哪些 detector candidate 有资格进入 future activation discussion
- 候选错误码何时才有资格从“更靠近 activation”进入真正的 activation skeleton 讨论

### 36.2 决策 1：`runtime-facing behavior activation` 的定义

#### 方案 A：仅 public exception / public API error / public control-flow / public fallback dispatch 前的最后 internal activation gate 属于 runtime-facing behavior activation

优点：

- 术语最清晰
- 最不容易把 internal carrying 误写成 external behavior
- 与当前 `runtime error surface`、`runtime-facing error gate`、`runtime-facing behavior gate` 的分层最一致

缺点：

- 需要额外说明哪些层只是邻接层而不是 activation 本体

风险：

- 推进显得更保守

#### 方案 B：更高层 internal mapping/gate/behavior-gate boundary 也算广义 runtime-facing behavior activation 邻接层

优点：

- 便于描述 future 过渡层

缺点：

- 容易把邻接层与 activation 本体混写

风险：

- 后续 AI 容易把 “near activation” 写成 “behavior already changed”

#### 方案 C：只要比 helper 更高层都算 runtime-facing behavior activation

优点：

- 叙述最省事

缺点：

- 几乎失去术语约束力

风险：

- 阶段口径最容易漂移

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- `runtime-facing behavior activation` 只指 public exception / public API error / public control-flow / public fallback dispatch 之前的最后一个 internal activation gate
- 它只表示 future 某个 internal owner deciding whether detector candidate may start to affect runtime-visible behavior
- 它是 runtime-facing behavior change 之前的最后 internal activation boundary

以下内容都 **不属于** runtime-facing behavior activation：

- helper 局部变量
- internal carried signal
- visible gate result
- mapping candidate
- runtime-facing error gate result
- runtime-facing behavior gate result
- tests / fixtures 中的 recommended error code

其中：

- `runtime-facing behavior gate`
  - 仍然只是更靠近 external behavior change 的最后 internal gate
- `runtime-facing behavior activation`
  - 则是更靠近 behavior change 真正开始生效前的最后 internal activation gate

两者都不等于 public behavior owner 本身。

不推荐方案 B 的原因：

- 会把 “邻接层” 和 “activation 本体” 混成一个术语

不推荐方案 C 的原因：

- 会直接摧毁当前 3-B 的分层精度

### 36.3 决策 2：detector result / behavior gate candidate 最小允许接近的层级

#### 方案 A：仍停在 internal runtime-facing behavior gate candidate

优点：

- 最保守

缺点：

- 会把 3-B.24 之后的推进完全停在原地

风险：

- 文档收敛不足以支撑下一轮最小 skeleton

#### 方案 B：进入 internal runtime-facing behavior activation boundary

优点：

- 能形成下一轮最小 skeleton 的清晰上限
- 仍然不触碰 public exception / API / control flow / fallback dispatch
- 与当前 `behavior_gate_candidate` 的更高层 internal carrying 连续

缺点：

- 需要持续强调 “接近 activation” 不等于 “activation 生效”

风险：

- 如果文档失守，容易被误读成 external behavior 已开始变化

#### 方案 C：进入 public exception / public response / public behavior surface 试探接近

优点：

- 推进最快

缺点：

- 已经不再是 activation discussion，而是 runtime-facing behavior change

风险：

- 会直接污染 public behavior 语义

#### 推荐结论

推荐 **方案 B**。

本轮固定：

- detector result / behavior gate candidate future 最多只允许 first approach：
  - 一个 **internal-only runtime-facing behavior activation boundary**
- 这一层最多只负责：
  - 消费 internal runtime-facing behavior gate candidate
  - 产出 internal activation candidate / no-op activation decision
- 它仍然 **不是**：
  - public exception owner
  - public API owner
  - parser / response_guard owner
  - control-flow owner
  - fallback / browser / JS owner

这也说明：

- “接近 runtime-facing behavior activation”
  - 只表示 future internal carrying 可以更靠近 behavior 变化前的最后 activation gate
- 它仍然不等于：
  - public behavior change 已发生
  - challenge/gateway 已会影响线上返回、抛错、分支或 fallback dispatch

不推荐方案 A 的原因：

- 它已经不足以支撑下一轮最小、可回退的内部结构推进

不推荐方案 C 的原因：

- 它已经直接越过 3-B.25 的决策边界

### 36.4 决策 3：哪些 detector candidate 可以进入 future runtime-facing behavior activation 讨论

#### 方案 A：只允许 challenge / gateway 进入 first-batch 讨论

优点：

- 与当前 detector first-batch sample、mapping candidate、runtime-facing gate candidate、behavior gate candidate 完全一致
- 语义相对收敛

缺点：

- 范围较窄

风险：

- 仍需持续防止被误写成 live support

#### 方案 B：再加 suspicious HTML

优点：

- 讨论覆盖面更广

缺点：

- 与 parser / stage / site semantics 耦合更强

风险：

- false positive 风险明显更高

#### 方案 C：再把 browser-required / js-required 也拉进来

优点：

- 看起来更完整

缺点：

- 已经把 3-B 讨论提前拖进 3-C / 3-D

风险：

- 阶段边界最容易失真

#### 推荐结论

推荐 **方案 A**。

本轮固定：

- future runtime-facing behavior activation discussion first-batch 只允许：
  - challenge
  - gateway
- 它们当前最多只允许以以下形式存在：
  - recommended only
  - internal mapping candidate
  - internal runtime-facing error gate candidate
  - internal runtime-facing behavior gate candidate
  - internal runtime-facing behavior activation candidate

以下内容当前继续排除在 discussion 之外：

- suspicious HTML
- browser-required
- js-required

原因是：

- suspicious HTML 仍然存在明显的误判风险与站点语义依赖
- browser/js-required 已经属于 future 3-C / 3-D 的讨论范围

不推荐方案 B 的原因：

- suspicious HTML 当前不足以稳定进入 activation 讨论

不推荐方案 C 的原因：

- browser/js-required 会直接把 3-B.25 讨论拖出当前阶段

### 36.5 决策 4：错误码何时才有资格进入 runtime-facing behavior activation 讨论

#### 方案 A：只要有 runtime-facing behavior gate candidate 就可进入 activation skeleton

优点：

- 推进快

缺点：

- 当前证据明显不够

风险：

- 最容易把 3-B.24 误写成 almost runtime-implemented

#### 方案 B：必须 additional evidence 齐全后才进入

优点：

- 与当前仓库事实最一致
- 能把 “internal carrying” 与 “future activation skeleton” 明确切开

缺点：

- 推进口径更保守

风险：

- 需要持续维护样本、回归与 no-regression 证据

#### 方案 C：等完整 detector live runtime 再讨论

优点：

- 最稳

缺点：

- 过度保守
- 会让最小 internal activation skeleton 无法顺序推进

风险：

- 把本可前置冻结的边界继续后移

#### 推荐结论

推荐 **方案 B**。

本轮固定：`LEGADO_ANTI_BOT_CHALLENGE` 与 `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 若 future 要进入真正的 runtime-facing behavior activation skeleton 讨论，至少还需要满足：

1. higher-layer carrying 已稳定存在，且 no-op 语义清晰
2. internal mapping candidate 已稳定存在
3. internal runtime-facing error gate candidate 已稳定存在
4. internal runtime-facing behavior gate candidate 已稳定存在
5. 正样本、负样本与 no-regression 回归矩阵已具备
6. challenge/gateway 的误判风险已有进一步收敛证据
7. activation-layer 的 owner、输入、输出与职责边界已冻结
8. public behavior change 尚未发生，但内部证据已经足够证明：
   - future activation boundary 仍然不是 public behavior owner
   - future activation boundary 仍然不会污染 parser / response_guard / API / exception surface / control flow / fallback dispatch

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

并且本轮不新增新的错误码 lifecycle 状态。

不推荐方案 A 的原因：

- 仅凭 runtime-facing behavior gate candidate 还不足以进入 activation skeleton 讨论

不推荐方案 C 的原因：

- 会把本可前置冻结的 activation 边界完全后移

### 36.6 决策 5：下一轮最小可执行任务

#### 方案 A：继续只做 runtime-facing behavior activation 文档设计

优点：

- 最保守

缺点：

- 3-B.25 已经把 activation 术语、上限和门槛冻结完了

风险：

- 再纯文档一轮会明显重复

#### 方案 B：进入 minimal runtime-facing behavior activation skeleton 实现（仅 internal activation contract / no-op activation）

优点：

- 与当前仓库证据链最连续
- 仍可保持 strict no-behavior-change
- 能验证 future activation boundary 的最小可回退结构

缺点：

- 需要更严格的命名、注释和 no-regression 测试

风险：

- 若口径失守，容易被误写成 “detector 结果已开始影响行为”

#### 方案 C：直接进入 detector 结果最小 runtime-facing behavior 生效实装

优点：

- 推进最快

缺点：

- 已经直接进入 runtime-facing behavior change

风险：

- 极易污染 public exception / API / parser / response_guard / control flow / fallback dispatch

#### 推荐结论

推荐 **方案 B**。

下一轮最小不可再小集合应固定为：

- 一个 internal-only runtime-facing behavior activation input / candidate / result / noop decision contract
- 一个 runtime-facing behavior gate candidate -> runtime-facing behavior activation candidate 的 no-op helper
- 一个 `source_engine.py` 邻接的 internal activation 调用点
- 对应的 no-behavior-change / no-exception-surface-change / no-api-surface-change / no-control-flow-change / no-fallback-dispatch-change 测试

下一轮仍然 **不允许** 进入：

- detector live runtime 生效
- runtime-facing behavior activation 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- parser / response_guard 联动
- anti-bot bypass
- browser / JS fallback

### 36.7 Step 1 / Step 2 判断

#### Step 1：如果本轮只做文档、决策与测试规划，是否已经足够

结论：**足够**。

原因：

- 当前仓库已经有足够证据证明 detector 结果最高只到 `runtime-facing behavior gate candidate / no-op gate decision`
- 当前最危险的歧义已经不在 helper 缺失，而在 activation 边界与 public behavior change 之间的术语关系
- 3-B.25 的目标就是把这条边界钉死，而不是继续增加 internal runtime 结构

#### Step 2：如果主张本轮必须落代码，是否已经有充分证明

结论：**没有**。

当前仍无法证明：

- 不落代码会阻塞下一轮
- 本轮存在一个最小不可再小、且不会被误写成 runtime-facing behavior change 的代码集合
- 本轮代码不会污染 `source_engine.py` 的对外返回/异常/控制流语义

因此 3-B.25 正确停留在：

- 文档
- Traceability
- 错误码状态
- 测试规划

而不进入 runtime-facing behavior activation skeleton 实装。

## 37. 3-B.26 detector runtime-facing behavior activation minimal skeleton 实现结论

### 37.1 当前 minimal runtime-facing behavior activation skeleton 的最小落点

按 3-B.25 已冻结的边界，本轮 minimal runtime-facing behavior activation skeleton 的代码落点固定为：

- `backend/app/schemas/online_detector_runtime_facing_behavior_activation.py`
- `backend/app/services/online/detector_runtime_facing_behavior_activation_skeleton.py`
- `backend/app/services/online/source_engine.py`

其中：

- `online_detector_runtime_facing_behavior_activation.py`
  - 只负责 internal activation input / candidate / result / noop decision contract
- `detector_runtime_facing_behavior_activation_skeleton.py`
  - 只负责 runtime-facing behavior gate candidate -> activation input -> activation result 的最小 no-op helper
- `source_engine.py`
  - 只在现有 runtime-facing behavior gate no-op 调用之后再追加一层更高层 internal activation carrying
  - 调用结果继续停留在 internal-only 层

本轮没有把 runtime-facing behavior activation 放进：

- `fetch_service.py`
- `response_guard_service.py`
- parser / content_parse

### 37.2 当前已落地什么

当前仓库已经以纯内部、纯 no-op、纯可回退的方式落地了：

- `DetectorRuntimeFacingBehaviorActivationInput`
- `DetectorRuntimeFacingBehaviorActivationCandidateKind`
- `DetectorRuntimeFacingBehaviorActivationCandidate`
- `DetectorRuntimeFacingBehaviorActivationResult`
- `DetectorRuntimeFacingBehaviorActivationOutcome`
- `DetectorRuntimeFacingBehaviorActivationDecision`
- minimal runtime-facing behavior activation helper
- source-engine 邻接更高层 runtime-facing behavior activation no-op 调用点
- runtime-facing behavior activation fixtures
- activation contract / helper / higher-layer activation candidate carrying / no-behavior-change tests

当前实际代码落点为：

- `backend/app/schemas/online_detector_runtime_facing_behavior_activation.py`
- `backend/app/services/online/detector_runtime_facing_behavior_activation_skeleton.py`
- `backend/app/services/online/source_engine.py`
- `backend/tests/fixtures/online_detector_runtime_facing_behavior_activation_samples.json`
- `backend/tests/test_online_detector_runtime_facing_behavior_activation_skeleton.py`

### 37.3 当前 runtime-facing behavior activation skeleton 允许做到什么

本轮当前只允许做到：

- internal activation input 被构造
- internal activation result 被构造
- detector result 被内部携带到一个更靠近 runtime-facing behavior activation 的 internal boundary
- activation helper 返回 no-op decision
- source-engine 邻接更高层位置内部调用 runtime-facing behavior activation helper

其中 current higher-layer activation carrying 只表达：

- challenge / gateway detector candidate 的 internal activation candidate carrying
- 对应 recommended error code 仅作为 internal-only 信息
- 当前 helper 已经可以区分：
  - `no_activation_candidate`
  - `activation_candidate_carried`

### 37.4 当前 runtime-facing behavior activation skeleton 明确不做什么

本轮当前仍然 **没有** 落地：

- runtime-facing behavior activation 生效
- detector live runtime
- public exception surface 变化
- API 输出变化
- parser / content_parse 行为变化
- response_guard 行为变化
- control flow 变化
- fallback dispatch 变化
- browser / JS / retry 行为
- challenge/gateway live detection 上线

当前仍必须明确表述为 **不支持**：

- detector live runtime
- runtime-facing behavior activation 生效
- challenge / gateway 的线上 detector
- suspicious HTML runtime detector
- browser/js-required runtime detector
- anti-bot bypass
- JS / WebView / browser fallback

### 37.5 为什么这仍然不等于 runtime-facing behavior activation 生效

因为本轮新增 runtime-facing behavior activation 只做：

- internal activation candidate carrying
- no-op activation decision

它当前 **不**：

- 改 `fetch_service.py` 返回值
- 改 `response_guard_service.py` 分类结果
- 改 parser / content_parse 行为
- 改 router / importer / DB / frontend
- 改异常 surface
- 改 API error body / response shape
- 改 control flow
- 改 fallback dispatch
- surface detector 错误码到 runtime path

并且 `source_engine.py` 中的 runtime-facing behavior activation helper 调用仍被内部 no-op guard 包裹：

- 即便 activation helper 本身异常
- 既有返回值与既有异常 surface 仍保持原样

因此本轮正确口径必须是：

> minimal runtime-facing behavior activation skeleton implemented internally, runtime-facing behavior activation behavior still unchanged

### 37.6 错误码状态结论

本轮没有新增 detector 错误码 lifecycle 状态。

本轮仍继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

本轮也不引入：

- `internal_activation_candidate`
- `activation_ready`
- `external_activation_ready`
- `runtime-implemented`

作为错误码 lifecycle 新状态。

原因是：

- 当前 runtime-facing behavior activation skeleton 只证明“candidate 被更高层 internal activation boundary 看见了”
- 并没有证明 detector 错误码已经会对外抛出
- 更没有证明 runtime behavior 已经被改变

### 37.7 下一步最小任务

在 3-B.26 之后，最小的下一步建议应是：

- **Phase 3-B.27：detector runtime-facing behavior effect 决策轮**

该轮只应继续回答：

- 哪类 internal activation candidate future 有资格进入真正的 runtime-facing behavior effect 讨论
- runtime-facing behavior activation 与 public exception / API / parser / response_guard / control-flow / fallback dispatch 的真实接缝应该如何定义
- 为什么仍然不能直接进入 challenge/gateway live support 或 anti-bot bypass

在这一步之前，仍不应直接进入：

- detector live runtime 正式支持
- runtime-facing behavior activation 生效
- detector 错误码对外抛出
- challenge/gateway live detection 上线
- browser/js fallback
- anti-bot bypass
