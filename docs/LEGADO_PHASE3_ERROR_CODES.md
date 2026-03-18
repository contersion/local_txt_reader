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

以下错误码按 3-B.1 决策轮，分为三类：

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
| `LEGADO_REQUEST_RUNTIME_TIMEOUT` | request runtime timeout | candidate_for_first_implementation | 当前只有无错误码的通用 timeout 文本 | 3-B | 纯 HTTP / mock 超时即可稳定测试 |
| `LEGADO_REQUEST_RETRY_EXHAUSTED` | retry 已耗尽 | documented_only | 未实现 | 3-B | 当前仓库没有 retry 机制，不应先落空壳错误码 |
| `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` | 被 anti-bot gateway 阻断 | documented_only | 文档建模，未入代码枚举 | 3-B | detector 规则尚未冻结，不建议首批进入代码 |
| `LEGADO_ANTI_BOT_CHALLENGE` | 触发反爬挑战 | documented_only | 已在代码枚举中预留，但未激活 | 3-B | challenge detector 尚未实现，不建议首批激活 |
| `LEGADO_SUSPICIOUS_HTML_RESPONSE` | 检测到可疑 HTML 响应 | documented_only | 文档建模，未入代码枚举 | 3-B | detector 规则尚未冻结，不建议首批进入代码 |
| `LEGADO_UNSUPPORTED_SIGNATURE_FLOW` | 不支持的签名流程 | implemented | 已进入 `online_runtime.py` 与 `request_profile_service.py` | 3-B.2 | 当前只做占位识别与拒绝分类，不做求值 |

### 3.3 运行环境层

| 错误码 | 含义 | 生命周期状态 | 公共路径状态 | 说明 |
| --- | --- | --- | --- | --- |
| `LEGADO_BROWSER_STATE_REQUIRED` | 需要浏览器态 | deferred | not_activated | 明确延后到 3-D |
| `LEGADO_JS_EXECUTION_REQUIRED` | 需要 JS 执行 | deferred | not_activated | 明确延后到 3-C |

### 3.4 反爬与限制层

| 错误码 | 含义 | 生命周期状态 | 公共路径状态 | 说明 |
| --- | --- | --- | --- | --- |
| `LEGADO_RATE_LIMITED` | 触发限流 | candidate_for_first_implementation | not_activated | 未来识别到 429 或稳定限流信号时使用 |

## 4. 当前实现范围

本轮只允许以下错误码进入最小骨架实现：

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
- Phase 3-B 新增的 request runtime / anti-bot classification 错误码当前仍停留在文档设计阶段

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

以下 2 个仍保留为首批候选，但当前尚未进入代码：

- `LEGADO_REQUEST_RUNTIME_TIMEOUT`
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

## 5. 当前不实现但必须预留的错误码

以下错误码当前保留为 `documented_only`，不进入当前代码：

- `LEGADO_LOGIN_FAILED`
- `LEGADO_COOKIE_INVALID`
- `LEGADO_AUTH_REQUIRED`
- `LEGADO_SESSION_INJECTION_FAILED`
- `LEGADO_UNSUPPORTED_ADVANCED_AUTH`
- `LEGADO_REQUEST_PROFILE_INVALID`
- `LEGADO_REQUEST_RETRY_EXHAUSTED`
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
- `LEGADO_ANTI_BOT_CHALLENGE`
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
- 当前仍属于首批候选，但尚未进入代码：
  - `LEGADO_REQUEST_RUNTIME_TIMEOUT`
  - `LEGADO_RATE_LIMITED`
- 当前只保留文档，不建议首批进入代码
  - `LEGADO_REQUEST_PROFILE_INVALID`
  - `LEGADO_REQUEST_RETRY_EXHAUSTED`
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
  - `LEGADO_SUSPICIOUS_HTML_RESPONSE`
- 明确后置
  - `LEGADO_JS_EXECUTION_REQUIRED`
  - `LEGADO_BROWSER_STATE_REQUIRED`

## 7. 编码约定

Phase 3 错误码遵循以下约定：

- 保持 `LEGADO_` 前缀，便于与现有 Phase 2 文档和前端错误展示保持一致
- 尽量使用“能力 + 结果”的稳定命名
- 不把 HTTP 状态码直接编码进错误码名称

## 8. 维护约定

1. 新增 Phase 3 运行时错误码时，必须同时更新本文件
2. 如果错误码进入真实实现，必须把状态更新为 `implemented`，并同步移出 `candidate_for_first_implementation` / `documented_only` / `deferred`
3. 如果新增错误码对应了新模块，还必须同步更新 `LEGADO_PHASE3_TRACEABILITY_INDEX.md`
