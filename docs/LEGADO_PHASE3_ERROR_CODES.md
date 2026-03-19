# Legado Phase 3 Error Codes

## 1. 适用范围

本文件定义 Phase 3 运行时能力的错误码分层设计，覆盖：

- 登录失败
- 会话缺失
- Cookie 失效
- 会话过期
- 需要认证
- 认证配置错误
- 会话注入失败
- 暂不支持的高级认证方式
- 需要浏览器态
- 需要 JS 执行
- 触发反爬 / 限流

本文件同时区分：

- `已实现错误码`
- `候选首批错误码`
- `仅文档保留错误码`
- `延后错误码`

## 2. 状态说明

- `implemented`
  - 当前仓库已有对应代码骨架，能够在有限场景下抛出
- `candidate_for_first_implementation`
  - 已完成 3-B.1 决策固定，适合作为下一轮最小实装入口，但当前尚未进入代码
- `skeleton_modeled`
  - 已进入内部静态骨架、fixture 或 classification result，但尚未接入 live runtime
- `seam_modeled`
  - 已进入 future live seam 所需的内部 summary / helper / fixture / contract 层，但尚未接入 live runtime
- `adapter_modeled`
  - 已进入 future live seam adapter 的内部 contract / helper / fixture / test 层，但尚未接入 live runtime
- `documented_only`
  - 当前仅在文档中建模或保留编号语义，不进入本轮代码
- `deferred`
  - 明确后置到 3-C / 3-D 或依赖尚不存在的高风险能力
- `reserved`
  - 当前只保留编号与语义，尚未实现
- `not_activated`
  - 代码路径已存在，但当前公共 router / API / 前端调用链还不会触发

## 2.1 当前公共路径说明

截至 Phase 3-A.1：

- `request_profile_service.py` 内部已经存在部分 runtime 错误码抛出逻辑
- 但当前 router / API / frontend 调用链没有公开传入 `auth_config` / `session_context`
- 因此即便代码路径存在，这些错误码中的一部分也仍然属于“未激活”状态

## 3. 错误码分层

### 3.1 认证与会话层

| 错误码 | 含义 | 生命周期状态 | 公共路径状态 | 说明 |
| --- | --- | --- | --- | --- |
| `LEGADO_LOGIN_FAILED` | 登录失败 | reserved | not_activated | 未来登录流程失败时使用 |
| `LEGADO_SESSION_MISSING` | 会话缺失 | implemented | not_activated | 当前仅在 `request_profile_service.py` 的内部路径可触发 |
| `LEGADO_COOKIE_INVALID` | Cookie 失效 | reserved | not_activated | 未来 Cookie 失效或关键 Cookie 缺失时使用 |
| `LEGADO_SESSION_EXPIRED` | 会话过期 | implemented | not_activated | 当前仅在内部 runtime 组装路径可触发 |
| `LEGADO_AUTH_REQUIRED` | 需要认证 | reserved | not_activated | 未来远端返回认证要求但当前无认证流程时使用 |
| `LEGADO_AUTH_CONFIG_INVALID` | 认证配置错误 | implemented | not_activated | 当前仅在 `request_profile_service.py` 的内部校验中可触发 |
| `LEGADO_SESSION_INJECTION_FAILED` | 会话注入失败 | reserved | not_activated | 未来序列化 headers/cookies 或注入执行链失败时使用 |
| `LEGADO_UNSUPPORTED_ADVANCED_AUTH` | 暂不支持的高级认证方式 | reserved | not_activated | 用于多阶段认证、验证码、浏览器态登录等 |

### 3.2 Phase 3-B 请求描述与运行时分类层

以下错误码按 3-B.1 与 3-B.5 决策结果，分为三类：

- `candidate_for_first_implementation`
  - 下一轮最小实装可优先落地
- `documented_only`
  - 当前只建模，不建议进入首批代码
- `deferred`
  - 明确依赖 3-C / 3-D 或尚不存在的执行能力

| 错误码 | 含义 | 当前状态 | 当前仓库状态 | 阶段归属 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `LEGADO_REQUEST_PROFILE_INVALID` | request profile 配置错误 | documented_only | 文档建模，未入代码枚举 | 3-B | 作为 umbrella 语义保留，不建议首批直接落代码 |
| `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE` | 不支持的 request body mode | implemented | 已进入 `online_runtime.py` 与 `request_profile_service.py` | 3-B.2 | 当前用于拒绝未激活 mode 与非法 mode |
| `LEGADO_INVALID_HEADER_TEMPLATE` | 非法 header template | implemented | 已进入 `online_runtime.py` 与 `request_profile_service.py` | 3-B.2 | 当前只做静态结构/模板合法性校验 |
| `LEGADO_REQUEST_TIMEOUT` | request timeout | implemented | 已进入 `response_guard_service.py` 与 `fetch_service.py` | 3-B.3 | 纯 transport timeout 分类，不涉及 detector |
| `LEGADO_REQUEST_RETRY_EXHAUSTED` | retry 已耗尽 | documented_only | 未实现 | 3-B | 当前仓库没有 retry 机制，不应先落空壳错误码 |
| `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` | 被 anti-bot gateway 阻断 | adapter_modeled | 已进入 detector skeleton 与 adapter internal skeleton，未接 live runtime | 3-B.12 | 只表示内部 adapter 层已建模；3-B.13 / 3-B.14 进一步固定：minimal live entry 决策与 skeleton 实现本身都不构成升级条件 |
| `LEGADO_ANTI_BOT_CHALLENGE` | 触发反爬挑战 | adapter_modeled | 已进入 detector skeleton 与 adapter internal skeleton，未接 live runtime | 3-B.12 | 只表示内部 adapter 层已建模；3-B.13 / 3-B.14 进一步固定：minimal live entry 决策与 skeleton 实现本身都不构成升级条件 |
| `LEGADO_SUSPICIOUS_HTML_RESPONSE` | 检测到可疑 HTML 响应 | documented_only | 文档建模，未入代码枚举 | 3-B.5 | heuristic 空间仍过宽，当前只保留文档建模 |
| `LEGADO_UNSUPPORTED_SIGNATURE_FLOW` | 不支持的签名流程 | implemented | 已进入 `online_runtime.py` 与 `request_profile_service.py` | 3-B.2 | 当前只做占位识别与拒绝分类，不做求值 |

### 3.3 运行环境层

| 错误码 | 含义 | 生命周期状态 | 公共路径状态 | 说明 |
| --- | --- | --- | --- | --- |
| `LEGADO_BROWSER_STATE_REQUIRED` | 需要浏览器态 | deferred | not_activated | 明确延后到 3-D |
| `LEGADO_JS_EXECUTION_REQUIRED` | 需要 JS 执行 | deferred | not_activated | 明确延后到 3-C |

### 3.4 反爬与限制层

| 错误码 | 含义 | 生命周期状态 | 公共路径状态 | 说明 |
| --- | --- | --- | --- | --- |
| `LEGADO_RATE_LIMITED` | 触发限流 | implemented | 已进入 `response_guard_service.py` 与 `fetch_service.py` | 3-B.3 | 当前只对 HTTP 429 做 generic classification |

## 4. 当前实现范围

### 4.0 Phase 3-A / 3-A.1 已实现错误码

当前已在 runtime skeleton 中实现的前置校验错误码为：

- `LEGADO_SESSION_MISSING`
- `LEGADO_SESSION_EXPIRED`
- `LEGADO_AUTH_CONFIG_INVALID`

原因：

- 这三类错误都属于“本地可判定”的 runtime 前置校验
- 不依赖真正的登录流程
- 不依赖远端站点行为识别
- 不依赖 JS / WebView / 反爬模块

注意：

- “进入骨架实现”不等于“当前公共 API 已激活”
- 按当前仓库证据，这三个错误码只在内部 runtime 组装代码路径存在
- 只有最小 L2 preflight 与最小 generic response classification 进入了实现；detector / anti-bot 相关错误码仍停留在文档设计阶段

### 4.0.1 Phase 3-B.2 / 3-B.3 已实现错误码

当前已在 3-B 最小实现中进入代码的错误码为：

- `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
- `LEGADO_INVALID_HEADER_TEMPLATE`
- `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
- `LEGADO_REQUEST_TIMEOUT`
- `LEGADO_RATE_LIMITED`

其中：

- 前 3 个属于 L2 preflight
- 后 2 个属于最小 generic response classification

它们当前都只服务于内部 runtime 路径，不表示公共产品路径已正式支持复杂请求运行时。

## 4.1 3-B 首批错误码入代码标准

3-B 首批错误码只有同时满足以下条件，才值得进入代码：

- 可由纯 HTTP 流程或纯本地 preflight 判定
- 可稳定复现
- 可写单元测试
- 不依赖 JS / 浏览器 / 验证码
- 不改变 router / importer / 数据库 / 前端公共语义

## 4.2 3-B 首批候选错误码

按 3-B.2 当前仓库状态，第一批 3-B 错误码已有以下 3 个进入实现：

- `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
- `LEGADO_INVALID_HEADER_TEMPLATE`
- `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`

本轮额外进入实现的 2 个 generic response 错误码：

- `LEGADO_REQUEST_TIMEOUT`
- `LEGADO_RATE_LIMITED`

原因：

- 前三项属于纯本地 preflight 分类
- 后两项属于纯 HTTP / transport 级稳定分类
- 五项都可以不碰 JS / browser / captcha
- 五项都适合最小单测覆盖

## 4.3 3-B.2 当前已进入实现的错误码

当前 3-B.2 最小 preflight 实装已实际落地：

- `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
- `LEGADO_INVALID_HEADER_TEMPLATE`
- `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`

它们当前只服务于：

- 内部 request descriptor / runtime schema
- `request_profile_service` 的静态 preflight

它们当前仍然 **不表示**：

- body mode 已全部可执行
- header template 已可求值
- signature flow 已被支持

## 4.4 3-B.4 候选但未实现的 response_guard 扩展项

本轮决策后，以下两类能力的状态固定为：

| 候选项 | 当前状态 | 是否进入代码 | 说明 |
| --- | --- | --- | --- |
| empty response classification | deferred / on hold | 否 | 当前缺少稳定 generic 定义，误伤风险过高 |
| content-type mismatch classification | candidate (narrow only) | 否 | 仅在极窄条件下可能成立，当前不进入默认实装 |

重要约束：

- 以上两项都 **不是 implemented**
- 当前也 **不应** 被表述为“response_guard 已支持”
- detector / suspicious HTML / challenge / gateway detection 仍未开始

## 4.5 3-B.5 detector 候选错误码分层

本轮在 detector / anti-bot 边界设计中，进一步固定以下分层：

- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 当前状态：`candidate_for_first_implementation`
  - 含义：仅限 future detector classification
  - 当前 **不** 表示：
    - gateway bypass 已支持
    - 自动恢复执行已支持
- `LEGADO_ANTI_BOT_CHALLENGE`
  - 当前状态：`candidate_for_first_implementation`
  - 含义：仅限 future detector classification
  - 当前 **不** 表示：
    - challenge solving 已支持
    - 浏览器兜底已支持
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 当前状态：`documented_only`
  - 原因：heuristic 仍然过宽，最容易和 parser/stage/site semantics 混淆
- `LEGADO_JS_EXECUTION_REQUIRED`
  - 当前状态保持：`deferred`
  - 阶段归属：`3-C`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 当前状态保持：`deferred`
  - 阶段归属：`3-D`

重要约束：

- 上述状态变化只表示 detector 边界已固定
- 不表示 detector 已进入实现
- 不表示 anti-bot 绕过已支持
- 不表示 JS / browser runtime 已支持

## 4.6 3-B.6 detector 静态骨架与 first-batch 样本分层结论

本轮没有让 detector 候选错误码进入实现。

本轮只进一步固定了：

- 哪些候选错误码进入 first-batch sample matrix
- 哪些候选错误码继续停留在文档候选层
- 哪些候选错误码继续保持 deferred

### 4.6.1 进入 first-batch 默认样本的 detector 候选

- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 状态保持：`candidate_for_first_implementation`
  - 进入 first-batch 默认正向样本
- `LEGADO_ANTI_BOT_CHALLENGE`
  - 状态保持：`candidate_for_first_implementation`
  - 进入 first-batch 默认正向样本

原因：

- 这两类更容易收敛为 challenge/gateway 的最小 generic signal bundles
- 也更适合作为 first-batch detector skeleton 的最小正向分类目标

### 4.6.2 暂不进入 first-batch 默认样本的 detector 候选

- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 状态保持：`documented_only`
  - 当前不进入 first-batch 默认样本

原因：

- 它最容易和 parser/stage/site semantics 混淆
- 当前证据不足以把它压缩成稳定、低误伤的 first-batch 默认样本

### 4.6.3 继续 deferred 的 detector 侧能力

- `LEGADO_JS_EXECUTION_REQUIRED`
  - 状态保持：`deferred`
  - 当前不进入 first-batch 默认样本
  - 继续后置到 `3-C`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 状态保持：`deferred`
  - 当前不进入 first-batch 默认样本
  - 继续后置到 `3-D`

原因：

- 这两类更适合作为 detector 输出中的 deferred requirement hint
- 当前不应把它们提前包装成 first-batch detector skeleton 的默认正向目标

## 4.7 3-B.7 detector 静态骨架建模后的错误码状态

本轮进入代码的只是内部 detector static skeleton，因此 detector 相关错误码状态必须继续与 live runtime 分离。

### 4.7.1 当前已进入 skeleton_modeled 的错误码

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

它们当前之所以从 candidate 升为 `skeleton_modeled`，是因为：

- 已经进入内部 output schema 的 `recommended_error_code`
- 已经进入 first-batch sample fixtures
- 已经进入离线 classification skeleton 的测试覆盖

但它们当前 **仍不表示**：

- `fetch_service.py` 会抛出这些错误码
- `source_engine.py` 会消费 detector 结果
- challenge/gateway detector 已上线
- anti-bot 支持已存在

### 4.7.2 当前仍停留在 documented_only 的 detector 错误码

- `LEGADO_SUSPICIOUS_HTML_RESPONSE`

原因：

- 本轮没有实现 suspicious HTML skeleton
- 本轮也没有让 suspicious HTML 进入 first-batch 默认 fixtures

### 4.7.3 当前仍保持 deferred 的 detector 相关错误码

- `LEGADO_JS_EXECUTION_REQUIRED`
- `LEGADO_BROWSER_STATE_REQUIRED`

原因：

- 本轮静态骨架没有实现 browser/js-required 分类
- 它们仍然只作为 future deferred capability 概念存在

## 4.8 3-B.8 detector live 接缝决策后的错误码升级门槛

本轮进一步固定：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

当前都继续保持：

- `skeleton_modeled`

当前**不允许**因为离线 skeleton 已经能给出 `recommended_error_code`，就把它们升级为：

- `runtime-implemented`

### 4.8.1 方案比较结论

#### 方案 A：只要 skeleton 能推荐错误码就升级

不推荐。

原因：

- 会把离线 classification result 误写成 live runtime 已接通
- 会误导为 challenge/gateway 已经能在线触发

#### 方案 B：必须 live seam 已接通且稳定触发才升级

推荐。

原因：

- 与当前仓库真实边界一致
- 能保持 `recommended_error_code` 与 `runtime actually raises` 的口径区分
- 适合作为 challenge / gateway 的统一升级门槛

#### 方案 C：等完整 detector runtime 全部做完再升级

不推荐。

原因：

- 过于迟滞
- 不利于后续按最小 live classification 能力逐步推进

### 4.8.2 升级到 `runtime-implemented` 的统一条件

challenge / gateway 两类 detector 错误码都必须满足同一套门槛，才允许升级：

1. future live seam 已接通
2. live path 能稳定构造 normalized `DetectorInput`
3. live path 能稳定命中并 surface 对应错误码
4. 正样本与负样本都存在
5. 单元测试与至少一层集成/回归测试存在
6. 文档、Traceability 与错误码状态仍明确写清：
   - classification only
   - not bypass
   - not browser/js runtime support

只要上述任何一项仍未满足：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

就必须继续保持：

- `skeleton_modeled`

而不能升级为：

- `runtime-implemented`

## 4.9 3-B.9 detector live seam skeleton 决策后的错误码状态结论

本轮不新增任何 detector 错误码，也不改变以下状态：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - 继续保持：`skeleton_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 继续保持：`skeleton_modeled`
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 继续保持：`documented_only`
- `LEGADO_JS_EXECUTION_REQUIRED`
  - 继续保持：`deferred`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 继续保持：`deferred`

### 4.9.1 本轮额外固定的门槛前提

3-B.9 进一步明确：

- future live seam skeleton contract 被固定
- 并不等于 live seam 已接通
- `recommended_error_code` 继续不等于 runtime actually raises

因此在 4.8 的升级门槛之外，当前还必须继续满足以下前提，challenge/gateway 才有资格未来升级到 `runtime-implemented`：

1. dual-path summary contract 已形成稳定内部结构
2. success / error 两条路径的 summary normalization 都已存在
3. thin coordinator/adapter 边界已落实为内部结构，而不是只停在文档
4. 上述结构没有改变 public router / importer / DB / frontend 语义

只要这些前提还停留在文档或 skeleton 层：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

就必须继续停留在：

- `skeleton_modeled`

而不能被写成：

- `runtime-implemented`

## 4.10 3-B.10 internal seam skeleton 实装后的错误码状态结论

本轮进入代码的是：

- internal seam skeleton
- 而不是 detector live runtime

因此本轮不会让任何 detector 候选错误码升级到：

- `runtime-implemented`

### 4.10.1 当前状态保持不变的错误码

- `LEGADO_ANTI_BOT_CHALLENGE`
  - 当前继续保持：`skeleton_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 当前继续保持：`skeleton_modeled`
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 当前继续保持：`documented_only`
- `LEGADO_JS_EXECUTION_REQUIRED`
  - 当前继续保持：`deferred`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 当前继续保持：`deferred`

### 4.10.2 `seam_modeled` 与当前 detector 错误码的关系

本轮新增了 `seam_modeled` 这一状态语义，用来区分：

- 已经进入 detector static skeleton 的内容
- 与已经进入 live seam internal contract 的内容

但按当前仓库实现证据：

- challenge/gateway 错误码本身仍然只在 detector static skeleton 中被推荐
- 它们尚未进入 live seam runtime surface
- 本轮新增的 summary/helper/fixtures 也没有直接把这些错误码 surface 到 runtime path

因此当前最保守、最准确的口径仍然是：

- `LEGADO_ANTI_BOT_CHALLENGE` -> `skeleton_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` -> `skeleton_modeled`

而不是：

- `seam_modeled`

### 4.10.3 什么时候才可能进入 `seam_modeled`

只有当某个 detector 相关错误码已经进入：

- live seam internal summary/helper/adapter contract
- 且这种建模已超出单纯 static detector skeleton
- 但仍未进入 runtime path

才适合考虑标记为：

- `seam_modeled`

在当前 3-B.10 仓库状态下，尚无 detector 错误码满足这一条件。

## 5. 当前不实现但必须预留的错误码

以下错误码当前保留为 `documented_only`，不进入当前代码：

- `LEGADO_LOGIN_FAILED`
- `LEGADO_COOKIE_INVALID`
- `LEGADO_AUTH_REQUIRED`
- `LEGADO_SESSION_INJECTION_FAILED`
- `LEGADO_UNSUPPORTED_ADVANCED_AUTH`
- `LEGADO_REQUEST_PROFILE_INVALID`
- `LEGADO_REQUEST_RETRY_EXHAUSTED`
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`

以下错误码当前为 `deferred`：

- `LEGADO_JS_EXECUTION_REQUIRED`
- `LEGADO_BROWSER_STATE_REQUIRED`

## 6. 与 Phase 2 错误码的关系

Phase 2 错误码仍然负责 importer / validator 的静态边界，例如：

- `LEGADO_UNSUPPORTED_COOKIE`
- `LEGADO_UNSUPPORTED_AUTHORIZATION`
- `LEGADO_UNSUPPORTED_LOGIN_STATE`

Phase 3 错误码负责未来运行时阶段的动态错误，例如：

- session 为空
- session 已过期
- 认证配置不合法
- 站点要求浏览器态
- 触发反爬

换句话说：

- `Phase 2` 回答“这个书源配置能不能进入当前系统”
- `Phase 3` 回答“运行时为什么执行失败”

并且在 Phase 3-A.1 当前状态下：

- 这些“运行时为什么失败”的错误还主要服务于内部骨架与测试验证
- 还不能被表述为“当前公共产品路径已稳定支持”

## 6.1 Phase 3-B 当前额外结论

当前与 3-B 相关的错误码，按仓库证据可分为三类：

- 已完成 3-B.1 决策固定并具有稳定语义
  - `LEGADO_REQUEST_PROFILE_INVALID`
  - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
  - `LEGADO_INVALID_HEADER_TEMPLATE`
  - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
- 已进入当前 3-B.2 最小 preflight 实装：
  - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
  - `LEGADO_INVALID_HEADER_TEMPLATE`
  - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
- 已进入当前 3-B.3 最小 generic response_guard 实装：
  - `LEGADO_REQUEST_TIMEOUT`
  - `LEGADO_RATE_LIMITED`
- 已进入当前 3-B.5 detector future candidate 分层：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
- 已进入当前 3-B.6 first-batch 默认样本候选：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
- 已进入当前 3-B.7 skeleton-modeled：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
- 已在当前 3-B.8 固定 `runtime-implemented` 升级门槛：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
- 已在当前 3-B.9 固定 seam skeleton contract 前提：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
- 已在当前 3-B.10 落地 internal seam skeleton：
  - 不改变 challenge/gateway 的当前错误码状态
- 已在当前 3-B.12 落地 adapter internal skeleton：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
  - 当前升级为 `adapter_modeled`
- 当前只保留文档，不建议首批进入代码
  - `LEGADO_REQUEST_PROFILE_INVALID`
  - `LEGADO_REQUEST_RETRY_EXHAUSTED`
  - `LEGADO_SUSPICIOUS_HTML_RESPONSE`

## 4.11 3-B.11 adapter 接入前决策后的错误码状态结论

本轮只固定：

- future adapter 的职责边界
- future adapter 的接入前门槛

本轮**不**引入：

- live adapter
- runtime error surface 打通
- detector live runtime

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.11.1 当前状态继续保持不变

- `LEGADO_ANTI_BOT_CHALLENGE`
  - 继续保持：`skeleton_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - 继续保持：`skeleton_modeled`
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 继续保持：`documented_only`
- `LEGADO_JS_EXECUTION_REQUIRED`
  - 继续保持：`deferred`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 继续保持：`deferred`

### 4.11.2 为什么 adapter pre-integration 决策不构成升级条件

原因很直接：

- adapter responsibility boundary 被固定
  - 不等于 adapter 已接入
- adapter input/output contract 被确认“足够进入 skeleton”
  - 不等于 live path 已能稳定触发 detector 错误码
- adapter pre-integration decision
  - 不等于 runtime error surface 已冻结

因此即使 3-B.11 已经完成，challenge/gateway 仍然不能从：

- `skeleton_modeled`

升级为：

- `seam_modeled`
- `runtime-implemented`

### 4.11.3 adapter 接入前仍需满足的门槛

在现有 4.8 / 4.9 / 4.10 基础上，adapter 进入最小实现之前仍需继续满足：

1. adapter responsibility boundary 已固定
2. adapter 与 `source_engine.py` / `fetch_service.py` / `response_guard_service.py` / detector 的单向边界已固定
3. dual-path summary contract 已稳定
4. adapter 输入输出 contract 已被确认“只足够进入 skeleton，而非 live 接入”

即便以上条件成立，也仍然只够支持：

- 最小 adapter skeleton

而不够支持：

- detector live runtime
- detector 错误码升级

## 4.12 3-B.12 adapter internal skeleton 实装后的错误码状态结论

本轮进入代码的是：

- adapter internal skeleton
- 而不是 adapter live 接入

因此本轮仍然不会让 detector 候选错误码升级到：

- `runtime-implemented`

### 4.12.1 当前状态更新

在本轮之后，以下错误码从：

- `skeleton_modeled`

升级为：

- `adapter_modeled`

仅限：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

原因是：

- 它们现在不仅存在于 detector static skeleton
- 也已经进入 adapter internal contract / helper / fixtures / tests
- 但仍然没有进入 live path

### 4.12.2 为什么这仍然不等于 runtime 支持

`adapter_modeled` 只表示：

- future live seam adapter 所需的内部 contract 已能承载这些 detector 候选错误码

它**不**表示：

- adapter 已接入 `source_engine.py`
- adapter 已接入 `fetch_service.py`
- adapter 已接入 `response_guard_service.py`
- detector 已在 live path 中工作
- runtime 已会抛出这些错误码

因此 challenge/gateway 当前虽然高于：

- `skeleton_modeled`

但仍然远低于：

- `runtime-implemented`

### 4.12.3 当前仍保持不变的错误码

- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - 继续保持：`documented_only`
- `LEGADO_JS_EXECUTION_REQUIRED`
  - 继续保持：`deferred`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 继续保持：`deferred`

### 4.12.4 adapter-modeled 之后仍需满足的条件

即使 challenge/gateway 已进入 `adapter_modeled`，仍然至少还差以下条件，才有资格未来升级到 `runtime-implemented`：

1. adapter live 接入位置已冻结
2. adapter live wiring 已存在
3. detector 输出与 runtime error surface 关系已冻结
4. live path 可稳定触发 challenge/gateway
5. live no-regression 证明存在

只要上述任一项未满足：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

而不能升级为：

- `runtime-implemented`
- 明确后置
  - `LEGADO_JS_EXECUTION_REQUIRED`
  - `LEGADO_BROWSER_STATE_REQUIRED`

## 4.13 3-B.13 adapter 最小接入决策后的错误码状态结论

本轮只固定：

- future minimal live entry 的定义
- future 最小 wiring 点
- future allowed / disallowed behaviors
- detector 错误码接近 runtime 的统一门槛

本轮**不**引入：

- adapter live wiring
- detector live runtime
- runtime error surface 变更

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.13.1 challenge / gateway 当前状态继续保持不变

以下错误码继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
  - `adapter_modeled`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `adapter_modeled`

原因是：

- 它们当前虽然已经进入 adapter internal contract / helper / fixture / test
- 但 future minimal live entry 目前仍只是决策结论
- 当前还没有任何 live path 调用了 adapter
- 当前更没有任何 runtime path 会稳定 surface 这些错误码

### 4.13.2 为什么 3-B.13 不新增 `internal_observed` 生命周期状态

本轮评估过：

- 是否要在 `adapter_modeled` 与 `runtime-implemented` 之间新增一个正式生命周期状态

结论是：**当前不新增**。

原因：

- 当前仓库还没有真实 live wiring 证据
- 新状态会让 lifecycle 术语进一步膨胀
- 更容易把“内部可观察 recommended_error_code”误写成“runtime 已接通”

因此本轮更保守、也更准确的口径是：

- future minimal live entry 最多只允许内部观察 `recommended_error_code`
- 但错误码生命周期状态继续保持：
  - `adapter_modeled`

### 4.13.3 未来即使进入 minimal live-entry skeleton，也仍不自动升级

即使下一轮 future 进入最小 live-entry skeleton，实现了：

- `source_engine.py` 邻接 thin helper/coordinator
- internal no-op wiring
- adapter input/output 的 live-path 内部流转

challenge/gateway 仍然 **不应仅因这些结构存在** 就升级为：

- `runtime-implemented`

至少还需要继续满足：

1. live wiring 已真实存在且稳定
2. live path 中的 detector result 与 runtime error surface 关系已冻结
3. 正样本、负样本与 no-regression 证据存在
4. 文档、Traceability 与测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

## 4.15 3-B.15 behavior gating 决策后的错误码状态结论

本轮只固定：

- future behavior gating 的定义
- future minimal impact layer
- future detector 错误码接近 runtime 的 gating 门槛

本轮**不**引入：

- runtime-visible gating
- runtime error surface 变更
- detector 错误码对外抛出

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.15.1 challenge / gateway 当前状态继续保持 `adapter_modeled`

以下错误码继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

当前状态都仍然是：

- `adapter_modeled`

原因是：

- 3-B.14 当前只证明了 internal observation
- 3-B.15 当前只固定了 future gating boundary
- 当前既没有 runtime-visible gating
- 也没有 runtime error surface change

### 4.15.2 `internal surfaced signal` 不是新的错误码生命周期状态

本轮允许讨论 future：

- `internal surfaced signal`

但它只应被理解为：

- future gate-layer contract 语义

它**不应**被理解为：

- 新的错误码生命周期状态
- 更不应被理解为：
  - `runtime-implemented`

因此本轮继续不新增：

- `internal_observed`
- `internal_surfaced`
- 其他新的错误码 lifecycle 状态

### 4.15.3 future gating 后，错误码未来仍需单独过门

即使 future 进入 minimal gating skeleton，实现了：

- internal signal carrying
- no-op gate decision

challenge/gateway 仍然 **不应仅因这些结构存在** 就升级为：

- `runtime-implemented`

至少还需要继续满足：

1. gate-layer 与 runtime error surface 的关系已冻结
2. public behavior 变化已单独决策并实装
3. live path 可稳定触发可见行为，而不只是 internal signal
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

## 4.16 3-B.16 minimal gating skeleton 实装后的错误码状态结论

本轮进入代码的是：

- internal gate input contract
- internal gate result / carried signal / noop decision contract
- minimal gating helper
- source-engine 邻接 seam 的 internal signal carrying

本轮**不是**：

- runtime-visible gating
- runtime error surface 变更
- detector 错误码对外抛出

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.16.1 challenge / gateway 当前状态继续保持 `adapter_modeled`

以下错误码继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

当前状态都仍然是：

- `adapter_modeled`

原因是：

- 本轮虽然让 detector result 进入了 internal gate-layer
- 也虽然允许 internal signal carrying / no-op gate decision 存在
- 但 detector 结果仍然没有进入 runtime-visible gating
- 更没有进入 runtime error surface

### 4.16.2 `internal signal carrying` 不是新的错误码生命周期状态

本轮允许存在：

- internal signal carrying

但它只应被理解为：

- gate-layer internal contract 语义

它**不应**被理解为：

- 新的错误码生命周期状态
- 更不应被理解为：
  - `runtime-implemented`

因此本轮继续不新增：

- `internal_observed`
- `internal_surfaced`
- `signal_carried`
- 其他新的错误码 lifecycle 状态

### 4.16.3 future runtime-visible gating 前仍需满足的条件

即使 3-B.16 已完成 minimal gating skeleton，challenge/gateway future 若要靠近 runtime-visible layer，仍至少需要满足：

1. 哪类 gate result 允许 first become runtime-visible 已被单独决策
2. runtime-visible gating 与 error surface / API / parser 的关系已冻结
3. public behavior 变化已被单独评估并可稳定复现
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

## 4.17 3-B.17 runtime-visible gating 决策后的错误码状态结论

本轮只固定：

- future runtime-visible gating 的定义
- future minimal visible layer
- future detector 错误码接近 runtime surface 的门槛

本轮**不**引入：

- runtime-visible gating 代码
- runtime error surface 变更
- detector 错误码对外抛出

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.17.1 challenge / gateway 当前状态继续保持 `adapter_modeled`

以下错误码继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

当前状态都仍然是：

- `adapter_modeled`

原因是：

- 3-B.16 当前只证明了 gate-layer internal carrying
- 3-B.17 当前只固定了 future runtime-visible boundary
- 当前既没有 runtime-visible gating 代码
- 也没有 runtime error surface change

### 4.17.2 higher-layer internal carrying 不是新的错误码生命周期状态

本轮允许讨论 future：

- higher-layer internal carrying
- internal surfaced near runtime

但它们只应被理解为：

- future runtime-visible gate boundary 的行为语义

它们**不应**被理解为：

- 新的错误码生命周期状态
- 更不应被理解为：
  - `runtime-implemented`

因此本轮继续不新增：

- `internal_observed`
- `internal_surfaced`
- `internal_carried`
- `internal_surfaced_near_runtime`
- 其他新的错误码 lifecycle 状态

### 4.17.3 future runtime-visible gating 后，错误码仍需单独过门

即使 future 进入 minimal runtime-visible gating skeleton，实现了：

- 更高层 internal boundary carrying
- internal surfaced-near-runtime signal

challenge/gateway 仍然 **不应仅因这些结构存在** 就升级为：

- `runtime-implemented`

至少还需要继续满足：

1. 哪类 internal gate result 允许 first become runtime-visible 已被单独决策
2. runtime-visible gating 与 error surface / API / parser 的关系已冻结
3. public behavior 变化已被单独评估并可稳定复现
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

## 4.14 3-B.14 live-entry skeleton 实装后的错误码状态结论

本轮进入代码的是：

- internal live-entry skeleton helper
- `source_engine.py` 邻接 seam 的 internal no-op wiring

本轮**不是**：

- detector live runtime
- runtime error surface 变更
- adapter live 结果对外生效

因此本轮不会让任何 detector 候选错误码升级为：

- `runtime-implemented`

### 4.14.1 challenge / gateway 当前状态继续保持 `adapter_modeled`

以下错误码继续保持：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

当前状态都仍然是：

- `adapter_modeled`

原因是：

- 本轮虽然让 live path 内部出现了 no-op wiring
- 也虽然允许内部 observation 看见 detector result
- 但 detector result 仍然没有进入 runtime error surface
- 仍然没有改变 API / parser / response_guard / fallback 行为

### 4.14.2 为什么本轮不新增 `live-entry-modeled`

本轮评估过是否要新增：

- `live-entry-modeled`

结论是：**当前不新增**。

原因：

- 当前生命周期术语已经足够表达仓库事实
- 新术语会增加文档与 Traceability 负担
- 更容易把“internal observation exists”误读成“runtime behavior changed”

因此本轮继续沿用：

- `adapter_modeled`

作为 challenge/gateway 当前最准确、最保守的状态表达。

### 4.14.3 未来升级前仍需满足的条件

即使 3-B.14 已完成最小 live-entry skeleton，challenge/gateway 未来要升级到：

- `runtime-implemented`

仍至少需要满足：

1. detector result 与 runtime error surface 的关系已冻结
2. public behavior change 的 gating 已单独决策完成
3. live path 可稳定触发 challenge/gateway，且不只是 internal observation
4. 正样本、负样本与 no-regression 证据存在
5. 文档、Traceability、测试继续明确：
   - classification only
   - not bypass
   - not browser/js runtime support

在这些条件满足之前：

- `LEGADO_ANTI_BOT_CHALLENGE`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`

都必须继续保持：

- `adapter_modeled`

## 7. 编码约定

Phase 3 错误码遵循以下约定：

- 保持 `LEGADO_` 前缀，便于与现有 Phase 2 文档和前端错误展示保持一致
- 尽量使用“能力 + 结果”的稳定命名
- 不把 HTTP 状态码直接编码进错误码名称

## 8. 维护约定

1. 新增 Phase 3 运行时错误码时，必须同时更新本文件
2. 如果错误码进入真实实现，必须把状态更新为 `implemented`，并同步移出 `candidate_for_first_implementation` / `documented_only` / `deferred`
3. 如果新增错误码对应了新模块，还必须同步更新 `LEGADO_PHASE3_TRACEABILITY_INDEX.md`
