# Legado Phase 3 Implementation Plan

## 总体目标

在不破坏现有本地 TXT 阅读与 Phase 2 回归链路的前提下，按阶段引入 Legado 高级兼容能力。

当前阶段只正式推进：

- `Phase 3-0`
- `Phase 3-A`
- `Phase 3-A.1`
- `Phase 3-B.1`
- `Phase 3-B.2`

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
