# Legado Phase 3 Traceability Index

## 状态标记说明

- `已设计`
  - 文档已明确边界，但当前仓库还没有对应代码骨架
- `decision-fixed`
  - 关键结构决策已固定，但当前仍未进入代码实现
- `designed`
  - 只有分层设计或预留模块，尚未固定到可直接起步的实现口径
- `not implemented`
  - 文档或决策已存在，但当前仓库没有对应实现
- `deferred to 3-C`
  - 明确后置到 JS 相关阶段
- `deferred to 3-D`
  - 明确后置到 browser/WebView 相关阶段
- `已骨架化`
  - 已有独立 schema / service / 注入点，但能力尚未正式对外支持
- `部分验证`
  - 已有代码与测试，但验证范围仍局限于骨架场景
- `未正式支持`
  - 仓库中有设计或代码钩子，但当前不应对外宣称能力可用
- `非生产就绪`
  - 仅适用于开发/骨架阶段，缺少持久化、多实例、一致性或安全保障
- `已正式支持`
  - 有稳定实现、测试与用户可用入口
- `未实现`
  - 尚未设计或尚未进入当前阶段

## Router / API 暴露状态说明

- `未暴露`
  - 现有公共 router / request schema / frontend 调用完全不感知该能力
- `内部可选钩子`
  - 仅在 service 层作为可选参数存在，默认调用链不使用
- `已暴露`
  - 当前公共 API 已直接暴露该能力

## 能力追踪索引

| 能力 | 当前阶段 | 实现状态 | 验证状态 | 支持状态 | API 暴露状态 | 后端模块 | 文档 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Session context schema | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` |
| Auth runtime schema | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py` | `LEGADO_PHASE3_ARCHITECTURE.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_session_runtime.py` |
| Session handler | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 未暴露 | `backend/app/services/online/session_handler.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` |
| Session storage abstraction | 3-A | 已骨架化 | 部分验证 | 非生产就绪 | 未暴露 | `backend/app/services/online/session_handler.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` |
| Cookie 注入扩展点 | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 内部可选钩子 | `backend/app/services/online/request_profile_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` |
| 请求画像装配 | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 内部可选钩子 | `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` |
| source engine 可选 session 注入 | 3-A | 已骨架化 | 部分验证 | 未正式支持 | 内部可选钩子 | `backend/app/services/online/source_engine.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | 复用在线 discovery 回归测试 |
| Router/API 公开认证参数 | 3-A.1 | 未实现 | 已核查 | 未正式支持 | 未暴露 | 无 | `LEGADO_PHASE3_ARCHITECTURE.md` | 复用在线 discovery / online books API 回归测试 |
| 会话持久化到数据库 | 3-A | 已设计 | 未实现 | 未正式支持 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 |
| 登录流编排 | 3-A | 已设计 | 未实现 | 未正式支持 | 未暴露 | `auth_flow_service` 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 |
| Cookie 失效与刷新策略 | 3-A | 已设计 | 未实现 | 未正式支持 | 未暴露 | 待定 | `LEGADO_PHASE3_ERROR_CODES.md` | 未实现 |
| request body mode enum 与挂载层 | 3-B.2 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` |
| header template 挂载层 | 3-B.2 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` |
| signature placeholder 边界 | 3-B.2 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` |
| response_guard 分层 | 3-B.1 | decision-fixed | not implemented | 未正式支持 | 未暴露 | `response_guard_service` | `LEGADO_PHASE3B_DECISIONS.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | timeout / rate limit 规划测试 |
| anti_bot_detector 分层 | 3-B.1 | decision-fixed | not implemented | 未正式支持 | 未暴露 | `anti_bot_detector` | `LEGADO_PHASE3B_DECISIONS.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | gateway / challenge / suspicious HTML 规划测试 |
| 第一批 3-B 错误码选择 | 3-B.2 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` |
| 复杂请求 / 基础反爬 | 3-B | 已设计 | 未实现 | 未正式支持 | 未暴露 | `anti_bot_handler` 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 |
| 受限 JS 沙箱 | 3-C | 已设计 | 未实现 | 未正式支持 | 未暴露 | `js_execution_sandbox` 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 |
| 浏览器态 / WebView 兜底 | 3-D | 已设计 | 未实现 | 未正式支持 | 未暴露 | `browser_fallback_service` 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 |

## Phase 3-B 请求运行时追踪链

| 能力层 | 能力 | 当前状态 | 目标模块 | 文档 | 测试规划 |
| --- | --- | --- | --- | --- | --- |
| L0 | 普通 HTTP GET/POST | 已正式支持 | 复用 `fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 复用现有 online discovery / online books 回归 |
| L1 | Session / Cookie / Header 注入 skeleton | skeleton only | 复用 `request_profile_service.py` / `session_handler.py` | `LEGADO_PHASE3_ARCHITECTURE.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | `backend/tests/test_online_session_runtime.py` |
| L2 | body mode / request description / 参数装配 | implemented (minimal preflight only) | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` |
| L3 | timeout / retry / rate limit / suspicious HTML / challenge 检测 | decision-fixed / not implemented | `response_guard_service`, `anti_bot_detector` | `LEGADO_PHASE3B_DECISIONS.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | timeout / rate limited 首批测试；gateway/challenge/suspicious HTML 后续规划 |
| L4 | JS 依赖能力 | deferred to 3-C | `js_execution_sandbox` | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | deferred |
| L5 | 浏览器态 / WebView | deferred to 3-D | `browser_fallback_service` | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | deferred |

## 能力 -> 模块 -> 文档 -> 测试

### Session / Cookie / 登录态

| 能力 | 模块 | 文档 | 测试 | 当前口径 |
| --- | --- | --- | --- | --- |
| SessionContext / SessionCookie | `backend/app/schemas/online_runtime.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` | 已骨架化 / 部分验证 / 未正式支持 |
| OnlineAuthConfig | `backend/app/schemas/online_runtime.py` | `LEGADO_PHASE3_ARCHITECTURE.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_session_runtime.py` | 已骨架化 / 部分验证 / 未正式支持 |
| Session resolve/save/clear | `backend/app/services/online/session_handler.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` | 已骨架化 / 部分验证 / 非生产就绪 |
| Request profile merge | `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` | 已骨架化 / 部分验证 / 内部钩子 |
| HTTP cookies injection | `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_session_runtime.py` | 已骨架化 / 部分验证 / 内部钩子 |
| discovery runtime hook | `backend/app/services/online/source_engine.py` | `LEGADO_PHASE3_ARCHITECTURE.md` | `backend/tests/test_online_discovery_api.py` | 已骨架化 / 部分验证 / 公共 API 未激活 |

### Phase 3-B.1 决策固定项

| 能力 | 模块 | 文档 | 测试 | 状态 |
| --- | --- | --- | --- | --- |
| request body mode | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` | implemented / partial validation / still preflight-only |
| header template | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` | implemented / partial validation / static-only |
| signature placeholder | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` | implemented / partial validation / classification-only |
| response_guard | `response_guard_service` | `LEGADO_PHASE3B_DECISIONS.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | timeout / rate limit 规划测试 | decision-fixed / not implemented |
| anti_bot_detector | `anti_bot_detector` | `LEGADO_PHASE3B_DECISIONS.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | suspicious HTML / gateway / challenge 规划测试 | decision-fixed / not implemented |
| first-batch 3-B error codes | `backend/app/schemas/online_runtime.py`, `backend/app/services/online/request_profile_service.py` | `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_request_preflight.py` | partially implemented |

### 反爬 / JS / WebView

| 能力 | 模块 | 文档 | 测试 | 状态 |
| --- | --- | --- | --- | --- |
| anti-bot handler | 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 | designed |
| JS execution sandbox | 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 | deferred to 3-C |
| browser fallback | 预留 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 未实现 | deferred to 3-D |

## Phase 3-B 设计状态口径

| 项目 | 当前口径 |
| --- | --- |
| request runtime | designed |
| request body mode | implemented / preflight-only |
| header template | implemented / static validation only |
| signature placeholder | implemented / classification only |
| request profile 增强 | skeleton only |
| response guard | decision-fixed / not implemented |
| anti-bot detection | decision-fixed / not implemented |
| anti-bot bypass | not formally supported |
| JS runtime | deferred to 3-C |
| browser fallback | deferred to 3-D |

## 与 Phase 2 的边界追踪

| 项目 | 当前归属 | 说明 |
| --- | --- | --- |
| `LEGADO_UNSUPPORTED_COOKIE` / `LEGADO_UNSUPPORTED_LOGIN_STATE` importer 拒绝 | Phase 2 | 继续表示“当前 importer 不接受高风险字段” |
| Session / Cookie runtime schema | Phase 3-A | 只表示“运行时骨架存在”，不表示 importer 已放开 |
| 登录流程 / Cookie 持久化 / 反爬 / JS / WebView | Phase 3-B / 3-C / 3-D | 当前只有设计，没有正式支持 |

## 本轮验收关联

当前 3-B.2 最小 preflight 实装的最小验收链为：

1. `RequestBodyMode` / `RequestRuntimeDescriptor` 已存在
2. header template preflight 已存在
3. signature placeholder preflight 已存在
4. 3 个错误码已进入实现：
   - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
   - `LEGADO_INVALID_HEADER_TEMPLATE`
   - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
5. `backend/tests/test_online_request_preflight.py` 已覆盖最小 preflight 场景
6. 旧 runtime skeleton / discovery / online books / online sources / importer 回归继续通过
7. `response_guard / anti_bot_detector / 3-C / 3-D` 仍未进入实现
