# Legado Phase 3-B Request Runtime Design

## 1. 文档定位

本文档只服务于 **Phase 3-B 强约束设计阶段**。

当前轮次进一步固定为：

- `Phase 3-B.1`：实装前决策轮
- 默认结论：只做决策、文档、Traceability、错误码分层更新
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

但该实现仍然严格限定在：

- L2 request descriptor / runtime schema
- 发请求前的静态校验
- 3 个最小错误码分类

并且仍然 **不等于**：

- response guard 实装
- anti-bot detector 实装
- JS / WebView / browser fallback 实装

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
- `LEGADO_REQUEST_RUNTIME_TIMEOUT`
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
