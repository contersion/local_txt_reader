# Legado Phase 3 Implementation Plan

## 总体目标

在不破坏现有本地 TXT 阅读与 Phase 2 回归链路的前提下，按阶段引入 Legado 高级兼容能力。

当前阶段只正式推进：

- `Phase 3-0`
- `Phase 3-A`
- `Phase 3-A.1`
- `Phase 3-B.1`
- `Phase 3-B.2`
- `Phase 3-B.3`
- `Phase 3-B.4`
- `Phase 3-B.5`
- `Phase 3-B.6`
- `Phase 3-B.7`
- `Phase 3-B.8`

## 阶段拆分

### Phase 3-0：项目扫描与架构设计

#### 目标

- 扫描后端 `routers / services / models / schemas`
- 扫描前端在线书源管理、书架、详情、阅读页、stores、api
- 明确本地 TXT 链路与在线阅读链路的边界
- 形成 Phase 3 文档、追踪索引、错误码分层与回退策略

#### 不做什么

- 不改 discovery 主链
- 不实现登录流程
- 不实现 Cookie 运行时
- 不引入 JS / WebView / 反爬绕过

#### 依赖关系

- 依赖现有 `AGENTS.md`
- 依赖 `development-process.md`
- 依赖 `docs/IMPLEMENTATION_STEPS.md`
- 依赖所有 Phase 2 文档与测试基线

#### 验收标准

- 新增 Phase 3 架构文档
- 新增 Phase 3 实施计划
- 新增 Phase 3 traceability 索引
- 新增 Phase 3 错误码草案
- 明确列出可复用模块、必改模块、建议新增模块、风险点、暂缓项

#### 风险点

- 扫描不完整会导致后续把扩展点插到错误层次
- 文档分层不清会让 Phase 2 与 Phase 3 边界重新混淆

### Phase 3-A：Session / Cookie / 登录态基础设施

#### 目标

- 定义 session / cookie / auth runtime 的基础 schema
- 增加 session storage abstraction
- 增加 request profile 装配层
- 给在线请求执行链增加可选 session 注入点
- 为未来登录型书源预留扩展点

#### 不做什么

- 不实现完整登录流程
- 不实现自动登录表单编排
- 不实现浏览器态登录
- 不实现完整 Cookie 持久化
- 不开放高风险 importer 字段兼容

#### 依赖关系

- 依赖 Phase 3-0 文档
- 依赖现有 `source_engine` / `fetch_service`
- 依赖 Phase 2 既有 discovery 与 importer 测试基线

#### 验收标准

- 存在独立 runtime schema
- 存在独立 session handler / storage abstraction
- 存在 request profile service
- `fetch_service` 支持可选 cookies 注入
- `source_engine` 支持可选 session context / auth config 扩展点
- 新增最小测试覆盖 session 注入与缺失/过期场景
- 无 session 时既有在线 discovery 逻辑保持兼容

#### 风险点

- 如果 request profile 与 fetch 执行层耦合过深，会抬高后续 anti-bot / JS 接入成本
- 如果这轮就做 DB 持久化，会把低风险骨架变成迁移任务

### Phase 3-A.1：骨架收口与稳定性加固

#### 目标

- 收紧“已骨架化”与“已正式支持”的表述边界
- 明确 session storage、cookie 注入、auth config 的生命周期限制
- 核查 runtime 参数没有静默污染现有 router / API / discovery 主链
- 补齐保护性测试，证明旧调用方式继续可用

#### 不做什么

- 不进入 Phase 3-B
- 不实现完整登录流
- 不实现 Cookie 刷新与持久化
- 不实现 anti-bot / JS / browser fallback
- 不修改 importer 以接受高级运行时字段

#### 为什么要先收口再进 3-B

- 当前 Phase 3 仍然只是 skeleton；如果不先把文档、注释、测试和默认兼容路径收紧，后续 3-B 很容易在错误边界上继续叠复杂度
- 先收口可以明确哪些能力只是内部骨架、哪些能力已经过验证、哪些能力还没有公共 API 激活路径
- 这样进入 3-B 时，新增能力不会被误包装成“当前已经正式支持”

#### 验收标准

- 文档统一表述为 runtime skeleton / not production-ready / not formally supported
- Traceability 能区分 designed / skeleton implemented / partially validated / not formally supported
- 错误码文档能区分 implemented / reserved / not activated
- `source_engine` / `fetch_service` 的扩展参数保持可选，旧调用无需修改
- session handler 与 request injection 的保护性测试补齐
- 旧 discovery / online source / online books 回归继续通过

### Phase 3-B.1：实装前决策轮

#### 目标

- 固定 `request body mode` 的层次归属
- 固定 `header template / signature placeholder` 的边界
- 固定 `response_guard` 与 `anti_bot_detector` 的拆分方式
- 固定第一批真正允许进入代码的 3-B 错误码
- 为下一轮最小实装收敛入口

#### 不做什么

- 默认不落代码
- 不改 router / importer / 数据库 / 前端 / 主流程语义
- 不进入 retry/backoff 真正执行
- 不进入 template executor / signature engine
- 不进入 JS / browser fallback

#### 为什么先做这一轮

- 当前接缝已经存在，但 3-B 的关键结构含义还没钉死
- 如果直接实装，最容易把语义散落到 `schema / request_profile_service / fetch_service`
- 先做决策轮，下一轮才能把实装范围压缩到最小且可回退

#### 验收标准

- `docs/LEGADO_PHASE3B_DECISIONS.md` 已固定四个关键决策
- `docs/LEGADO_PHASE3B_REQUEST_RUNTIME.md` 已补清结构边界与“只识别不绕过”的口径
- `docs/LEGADO_PHASE3_TRACEABILITY_INDEX.md` 已能标记：
  - `designed`
  - `decision-fixed`
  - `not implemented`
  - `deferred to 3-C`
  - `deferred to 3-D`
- `docs/LEGADO_PHASE3_ERROR_CODES.md` 已区分：
  - `implemented`
  - `candidate for first implementation`
  - `documented only`
  - `deferred`

#### 当前轮次结论

当前对 3-B.1 的默认判断是：

> 仅文档与决策已经足够，不需要在本轮进入任何 3-B 代码实现。

### Phase 3-B：复杂请求 / 基础反爬

#### 目标

- 引入受控的 request profile 增强设计
- 评估基础限流、重试、挑战页识别与 anti-bot 钩子的分层位置
- 先把“请求描述能力”和“风险识别能力”从实现层剥离出来，形成可验证设计

#### 不做什么

- 不做 JS 引擎
- 不做浏览器渲染
- 不追求全站点兼容
- 本轮默认不落代码
- 不默认进入 3-B 实装

#### 依赖关系

- 依赖 Phase 3-B.1 已固定的四个结构决策
- 依赖 Phase 3-A 的 session / request profile 基础设施
- 依赖 Phase 3 错误码分层

#### 验收标准

- 已完成复杂请求问题分层
- 已完成模块边界、数据流、错误码与测试规划
- 已明确哪些问题只属于“检测”，不属于“绕过”
- 已明确哪些能力必须延后到 3-C / 3-D
- 进入实装前，四个关键决策必须已经是 `decision-fixed`

#### 风险点

- 反爬场景不可控，容易引入站点耦合逻辑

#### 当前轮次额外约束

本轮对 3-B 的默认策略是：

- 只做设计
- 默认不落代码
- 若要落代码，必须证明：
  - 仅设计不足以推进项目
  - 改动不触碰 router / importer / 数据库 / 前端语义 / 主流程语义
  - 只是最小占位骨架，且可以独立回退

按当前仓库现状，默认判断是：

> 仅设计已经足够推进项目，因此本轮应停在设计层。

#### 进入 3-B 实装前仍缺少的证据

- request body mode 的稳定 schema 决策
- header template / signature placeholder 的边界定义
- response guard 与 anti-bot detector 的职责拆分证据
- 旧链路零破坏验证的最小测试矩阵
- “识别”与“绕过”边界的稳定错误码口径

#### 下一轮若进入 3-B 实装，最小起步点是什么

默认建议从最小 preflight 入口开始，而不是直接进入复杂响应检测：

1. 内部 `request_runtime_schema` / `request descriptor`
2. `RequestBodyMode` enum
3. header template / signature placeholder 的最小静态分类
4. 仅为以下错误码补最小测试与实现：
   - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
   - `LEGADO_INVALID_HEADER_TEMPLATE`
   - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`

以上步骤完成前，不建议进入：

- `response_guard` 真正代码实现
- `anti_bot_detector` 真正代码实现
- retry/backoff
- challenge/gateway 检测

### Phase 3-B.2：最小 preflight 实装

#### 目标

- 把 3-B.1 已固定的 L2 结构，以最小、可回退、可单测方式落到代码
- 只覆盖：
  - request body mode
  - header template 静态校验
  - signature placeholder 占位识别与拒绝分类
- 保持旧 discovery / preview / online books / importer 链路不变

#### 已落地范围

- `RequestBodyMode` enum
- `RequestRuntimeDescriptor`
- `HeaderTemplateSpec`
- `SignaturePlaceholderSpec`
- `request_profile_service` 单点 preflight hook
- 3 个最小错误码：
  - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
  - `LEGADO_INVALID_HEADER_TEMPLATE`
  - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`

#### 明确不做什么

- 不做 json/raw body transport 实装
- 不做 header template 求值或执行
- 不做 signature engine
- 不做 response_guard
- 不做 anti_bot_detector
- 不做 timeout/retry/backoff/rate-limit 真实执行逻辑
- 不做 JS / browser fallback

#### 为什么这一步安全

- 改动只落在内部 schema 与 `request_profile_service`
- 无 descriptor 时旧链路完全按原逻辑运行
- 不改 public router schema
- 不改 importer 白名单
- 不改数据库

#### 验收标准

- 新增 preflight 测试覆盖：
  - body mode
  - header template
  - signature placeholder
  - 无 descriptor 的旧路径兼容
- 现有 runtime skeleton 测试继续通过
- 现有 discovery / online books / online sources / importer 回归继续通过

#### 当前结论

当前仓库已经完成：

> `Phase 3-B.2` 最小 preflight 实装

但仍然没有进入：

- detector / anti-bot / response_guard 实装
- 3-C
- 3-D

### Phase 3-B.3：generic response_guard 最小分类实装

#### 目标

- 在 3-B.2 的基础上，只增加最小 generic response classification
- 当前只覆盖：
  - transport timeout
  - HTTP 429
- 保持旧成功路径完全不变

#### 已落地范围

- `response_guard_service` 最小 helper
- `fetch_service` 单点 response_guard hook
- 2 个错误码：
  - `LEGADO_REQUEST_TIMEOUT`
  - `LEGADO_RATE_LIMITED`

#### 明确不做什么

- 不做 suspicious HTML 检测
- 不做 challenge / gateway / anti-bot detection
- 不做 retry / backoff / rate limit 执行策略
- 不做自动恢复 / fallback / 降级
- 不做 JS / browser runtime 判断

#### 为什么这一步安全

- timeout 与 429 都是纯 transport / 纯 HTTP 层信号
- 分类落点仍然局限在 `fetch_service` 附近
- 不依赖响应内容语义
- 不会把 transport 层升级成 anti-bot detector

#### 验收标准

- timeout 被稳定映射到 `LEGADO_REQUEST_TIMEOUT`
- 429 被稳定映射到 `LEGADO_RATE_LIMITED`
- 正常 2xx 响应不误触发
- preflight、runtime skeleton、discovery、online books、online sources、importer 回归继续通过

#### 当前结论

当前仓库已经完成：

> `Phase 3-B.3` generic response_guard 最小分类实装

但仍然没有进入：

- detector / anti-bot 实装
- suspicious HTML / challenge / gateway detection
- retry/backoff/rate-limit 执行策略
- 3-C
- 3-D

### Phase 3-B.4：response_guard 扩展前决策轮

#### 目标

- 判断 response_guard 是否还值得继续吸收新的 generic classification
- 判断哪些候选一旦再往前一步就会越界到 detector
- 为下一轮最小任务收敛边界

#### 默认策略

- 默认只做文档、Traceability、错误码分层与测试规划
- 默认不落代码

#### 本轮重点问题

- `empty response` 是否能稳定 generic 化
- `content-type mismatch / unacceptable response metadata` 是否值得继续进入 response_guard
- `response_guard` 与 `anti_bot_detector` 的文档边界是否还需要补钉
- 下一轮最小任务到底应不应该继续扩 response_guard

#### 当前结论

- `empty response`
  - 当前证据不足，**暂不进入 response_guard**
- `content-type mismatch`
  - 仅保留为**极窄候选**
  - 当前**不进入下一轮默认实装**
- 当前继续扩 response_guard 的收益已经很小
- 下一轮更合理的方向应是：
  - **detector 设计轮**
  - 而不是继续扩 response_guard 实装

#### 为什么本轮默认不落代码

- 当前仓库已经有足够证据做出上述判断
- 再写代码不会比文档决策提供更多必要信息
- 若硬把 empty response / content-type mismatch 拉进实现，最容易直接越界到 detector

### Phase 3-B.5：detector / anti-bot 边界设计轮
#### 目标

- 固定 detector 的问题范围，只覆盖响应后、且必须读取 body meaning / HTML semantics / challenge markers / gateway fingerprints / browser-js-required signals 的分类问题
- 固定 detector 与 `response_guard` 的调用顺序、输入输出边界与目录职责，防止 `response_guard` 继续膨胀成 detector
- 固定第一批 detector 候选能力与错误码状态，明确哪些只是 documented only，哪些才是 future candidate，哪些必须继续 deferred 到 3-C / 3-D
- 为下一轮最小任务收敛到 detector skeleton 的“实现前决策”，而不是直接进入 detector 代码

#### 默认策略

- 默认只做文档、Traceability、错误码分层与测试规划
- 默认不落代码

#### 本轮固定结论

- `response_guard` 当前只覆盖：
  - transport timeout
  - HTTP 429
  - 极少量稳定、纯 HTTP / metadata 级别的问题
- 任何需要读取以下内容的分类，都不再属于 `response_guard`：
  - response body meaning
  - HTML semantics
  - challenge wording
  - gateway / WAF fingerprints
  - browser-required / js-required body-level signals
- detector 当前只允许被设计为：
  - classification only
  - stop-execution only
  - no bypass
  - no recovery orchestration
- 第一批 detector 文档候选固定为：
  - suspicious HTML candidate
  - anti-bot challenge candidate
  - gateway / WAF interception candidate
  - browser-required candidate signal
  - js-required candidate signal
- 其中状态分层固定为：
  - `LEGADO_SUSPICIOUS_HTML_RESPONSE`：`documented_only`
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`：`candidate_for_first_implementation`
  - `LEGADO_ANTI_BOT_CHALLENGE`：`candidate_for_first_implementation`
  - `LEGADO_JS_EXECUTION_REQUIRED`：`deferred to 3-C`
  - `LEGADO_BROWSER_STATE_REQUIRED`：`deferred to 3-D`

#### 为什么本轮仍不进入 detector 实装

- 当前仓库还没有 detector 的最小输入/输出契约
- 当前仓库还没有 detector 的最小测试样本矩阵
- 当前仓库虽然已经有 `RawFetchResponse`，但还没有固定“在哪一层读取 body meaning”这件事的单点接缝
- 现在直接落 detector 代码，最容易把 heuristic、parser semantics、anti-bot 口径和 future recovery 语义混写在一起

#### 推荐的调用顺序

- `preflight`
- `fetch`
- `response_guard`
- `detector`
- `parser / content_parse`

#### 下一轮最小任务建议

- 不直接进入 detector 实装
- 优先进入：
  - **Phase 3-B.6：detector 最小静态分类骨架决策轮**
- 下一轮只应固定：
  - detector 输入契约
  - detector 输出契约
  - first-batch detector 样本矩阵
  - challenge / gateway 的最小 generic heuristic 边界

#### 当前阶段结论

本轮完成后，当前项目应继续表述为：

> `Phase 3-B.5` 已完成 detector / anti-bot 边界设计，仓库仍未进入 detector / anti-bot 实装，仍未进入 3-C / 3-D。

### Phase 3-B.6：detector 最小静态分类骨架决策轮
#### 目标

- 固定 detector 输入契约
- 固定 detector 输出契约
- 固定 first-batch sample matrix
- 固定 challenge / gateway 的最小 generic heuristic 边界

#### 默认策略

- 默认只做文档、Traceability、错误码状态与测试规划
- 默认不落代码

#### 本轮固定结论

- detector 不应直接依赖完整 `httpx.Response`
- detector 也不应直接依赖 parser 输出
- detector 的 future 输入应收敛为：
  - normalized detection input
  - 由 stage context + bounded response evidence summary 组成
- detector 的 future 输出应收敛为：
  - structured classification result
  - 再由上层映射错误码
- first-batch 正向样本只覆盖：
  - challenge candidate
  - gateway candidate
- `suspicious HTML`
  - 继续保留在文档候选层
  - 暂不进入 first-batch 默认样本
- `browser-required` / `js-required`
  - 继续只保留在文档候选与 deferred 状态层
  - 暂不进入 first-batch 默认样本
- challenge / gateway 的第一轮 heuristic 只允许：
  - 极少数 generic signal bundles
  - 不允许 site-specific 线索进入首轮边界

#### 为什么本轮仍然不进入 detector 代码

- 当前 `fetch_service.py` 在 `status_code >= 400` 时会提前抛错
- 这说明 detector 首先缺的是稳定输入载体，而不是 heuristic 代码
- 若现在直接落 detector service / hook，更容易把 transport、parser、heuristic 与 future recovery 混写在一起
- 当前没有充分证据证明 detector 空壳已经是“最小不可再小”

#### 下一轮若推进，最小入口应该是什么

推荐下一轮进入：

- **Phase 3-B.7：detector 最小静态分类骨架实现**

但范围必须继续收紧为：

- 只落内部 detector input schema
- 只落内部 detector output schema
- 只落 challenge/gateway first-batch sample fixtures
- 只落纯离线、可单测的静态分类骨架

当前仍不应直接进入：

- live detector hook
- suspicious HTML heuristic
- browser/js-required heuristic
- anti-bot bypass
- 3-C / 3-D

#### 若下一轮仍不落代码，项目是否仍可推进

可以，但收益会明显下降。

原因：

- 经过 3-B.5 与 3-B.6，detector 的边界、契约与样本范围已经足够清晰
- 若继续只做文档轮，理论上仍然合理，尤其当团队还想先收紧 sample governance
- 但默认建议是：3-B.6 之后文档层已经足够支撑下一轮进入最小离线骨架实现

#### 当前阶段结论

本轮完成后，当前项目应继续表述为：

> `Phase 3-B.6` 已完成 detector 最小静态分类骨架决策，仓库仍未进入 detector / anti-bot 实装，仍未进入 3-C / 3-D。

### Phase 3-B.7：detector 最小静态分类骨架实现
#### 目标

- 只落内部 detector input schema
- 只落内部 detector output schema / classification result
- 只落 challenge/gateway first-batch sample fixtures
- 只落纯离线、可单测的静态 classification skeleton

#### 默认策略

- 允许进入代码
- 但只允许内部 schema / fixtures / skeleton / tests
- 不接 live runtime

#### 已落地范围

- `backend/app/schemas/online_detector.py`
- `backend/app/services/online/detector_skeleton.py`
- `backend/tests/fixtures/online_detector_samples.json`
- `backend/tests/test_online_detector_skeleton.py`
- `backend/app/schemas/online_runtime.py`
  - 仅补充 `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 枚举项

#### 明确不做什么

- 不接 `fetch_service.py` live path
- 不接 `source_engine.py` live path
- 不实现 suspicious HTML detector
- 不实现 browser-required / js-required detector
- 不实现 anti-bot bypass
- 不实现 JS / browser fallback
- 不改 public router / importer / DB / frontend

#### 为什么这一步安全

- 改动范围完全局限于内部 schema、离线 fixtures、离线 skeleton 与测试
- 现有在线请求链没有接入任何 detector hook
- 现有 3-B.2 / 3-B.3 路径继续按原行为运行

#### 验收标准

- detector input schema 可单独构建与校验
- detector output schema 可表达：
  - `no_match`
  - `candidate_match`
  - `deferred`
- first-batch fixtures 可被稳定加载
- challenge / gateway 正样本命中
- 负样本不误命中
- `fetch_service.py` / `source_engine.py` 未接入 detector live path
- 3-B.2 / 3-B.3 与 online/import 回归继续通过

#### 当前阶段结论

本轮完成后，当前项目应继续表述为：

> `Phase 3-B.7` 已完成 detector 最小静态分类骨架实现，但仓库仍未进入 detector live runtime，仍未进入 anti-bot / browser / JS 实装，仍未进入 3-C / 3-D。

#### 下一轮最小入口建议

推荐下一轮进入：

- **Phase 3-B.8：detector live 接缝决策轮**

而不是直接进入：

- suspicious HTML runtime
- browser/js-required runtime
- anti-bot bypass

### Phase 3-B.8：detector live 接缝决策轮
#### 目标

- 固定 future detector live 输入从哪一层来
- 固定 future detector live hook 的最小接缝位置
- 固定 `fetch_service.py` 4xx/5xx 早抛错与 detector future 接入的兼容方向
- 固定 detector 错误码从 `skeleton-modeled` 升到 `runtime-implemented` 的门槛
- 为下一轮最小 live seam skeleton 继续收敛边界

#### 默认策略

- 默认只做文档、Traceability、错误码状态与测试规划
- 默认不落代码

#### 本轮固定结论

- future live detector 仍应继续消费 normalized `DetectorInput`
- `DetectorInput` 不应在 `fetch_service.py` 中直接构造
- `DetectorInput` 更适合由 future thin adapter / coordinator 在：
  - `fetch`
  - `parser`
  之间单点构造
- 这个接缝在逻辑上仍位于：
  - `source_engine.py`
  - `fetch_stage_response(...)` 之后
  - `parse_*_preview(...)` 之前
- `fetch_service.py` 当前的 `status_code >= 400` 早抛错，确实会阻断 future detector 对部分 challenge/gateway block page 的读取
- 下一轮若要继续推进，最小方向不应是 transport result 重构，而应优先固定：
  - future exception-to-summary / fetch-outcome adapter 的最小契约
- `LEGADO_ANTI_BOT_CHALLENGE`
  - 继续保持 `skeleton_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 继续保持 `skeleton_modeled`
- 它们只有在以下条件全部满足后，才允许升级到 `runtime-implemented`：
  - live seam 已接通
  - live path 能稳定构造 `DetectorInput`
  - live path 能稳定触发对应错误码
  - 正负样本齐备
  - 单测 / 集成回归齐备
  - 文档仍明确它们只是 classification，不是 bypass

#### 为什么本轮仍不进入 live detector 实装

- 当前仓库虽然已经足够决定 seam 方向，但还没有最小 fetch-outcome adapter 契约
- 当前仓库虽然已经足够证明 early raise 是 blocker，但还没有收敛到“最小不可再小”的 live seam skeleton
- 现在直接实装，最容易伤到：
  - `fetch_service.py`
  - `source_engine.py`
  - `parser/content_parse`
  的既有边界

#### 下一轮最小入口建议

推荐下一轮进入：

- **Phase 3-B.9：detector live seam skeleton 决策轮**

只收敛以下内容：

- future exception-to-summary / fetch-outcome adapter contract
- `source_engine.py` 调用 future thin coordinator 的最小边界
- detector live input summary 的最小字段保留规则
- 无 detector 命中时成功路径零破坏的最小测试矩阵

当前仍不应直接进入：

- detector live hook 实装
- suspicious HTML runtime
- browser/js-required runtime
- anti-bot bypass
- 3-C / 3-D

#### 当前阶段结论

本轮完成后，当前项目应继续表述为：

> `Phase 3-B.8` 已完成 detector live 接缝决策，仓库仍未进入 detector live runtime，仍未进入 anti-bot / browser / JS 实装，仍未进入 3-C / 3-D。

### Phase 3-C：受限 JS 沙箱

#### 目标

- 为少量高频 JS 规则提供受限执行能力
- 建立隔离、超时、资源限制与错误恢复策略

#### 不做什么

- 不做浏览器 DOM 全量模拟
- 不做无边界脚本执行

#### 依赖关系

- 依赖 Phase 3-B 的 request/runtime 分层
- 依赖更严格的错误码与 traceability

#### 验收标准

- JS 执行在独立沙箱模块中
- 存在超时、资源限制、失败回退
- 基础在线阅读链路不受影响

#### 风险点

- 安全风险高
- 调试成本显著上升

### Phase 3-D：WebView / 浏览器渲染兜底策略

#### 目标

- 为必须浏览器态才能工作的少量书源提供兜底策略
- 明确“哪些情况需要浏览器态，哪些情况继续拒绝”

#### 不做什么

- 不把浏览器态当成默认执行路径
- 不让 WebView 替代普通 HTTP 主链

#### 依赖关系

- 依赖 Phase 3-C 的错误归因与运行时隔离
- 依赖更高等级的资源控制策略

#### 验收标准

- browser fallback service 边界清晰
- 调用条件明确
- 不影响普通书源性能和稳定性

#### 风险点

- 资源消耗高
- 行为不可预测
- 平台耦合重

## 本轮最小代码计划

### 1. 文档

- 新增 `docs/LEGADO_PHASE3_ARCHITECTURE.md`
- 新增 `docs/LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`
- 新增 `docs/LEGADO_PHASE3_TRACEABILITY_INDEX.md`
- 新增 `docs/LEGADO_PHASE3_ERROR_CODES.md`
- 新增 `docs/LEGADO_PHASE3B_DECISIONS.md`

### 2. 测试

- 新增最小 preflight 单测
- 回归运行 online runtime / discovery / online books / online sources / importer 相关测试
- 全量 backend 测试应继续通过

### 3. 代码

- 在 `online_runtime.py` 增加最小内部 descriptor/schema
- 在 `request_profile_service.py` 增加单点 preflight hook
- 新增 preflight 测试文件

### 4. 验证

- 运行最小 preflight 单测
- 运行旧链路回归测试
- 运行全量 backend 测试
- 确认当前阶段结论仍为：
  - `Phase 3-B.2` 最小 preflight 已实现
  - `response_guard / anti_bot_detector` 仍未实现

## 本轮不做的代码范围

- 不改数据库结构
- 不改 importer 白名单边界
- 不改本地 TXT 阅读模型与语义
- 不做前端登录 UI
- 不做浏览器态兜底
- 不做登录型书源正式支持声明
