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
| generic response_guard 分层 | 3-B.3 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/services/online/response_guard_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_response_guard.py` |
| timeout classification | 3-B.3 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/services/online/response_guard_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_response_guard.py` |
| HTTP 429 classification | 3-B.3 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/services/online/response_guard_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_response_guard.py` |
| empty response classification | 3-B.4 | decision-fixed | not implemented | 暂缓 | 未暴露 | 待定 | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 仅测试规划，当前不进入实现 |
| content-type mismatch classification | 3-B.4 | decision-fixed | not implemented | 候选（极窄） | 未暴露 | 待定 | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | 仅测试规划，当前不进入实现 |
| response_guard / anti_bot_detector 边界补钉 | 3-B.4 | decision-fixed | not implemented | 文档已固定 | 未暴露 | `response_guard_service` / `anti_bot_detector` 边界 | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 设计轮，无代码测试 |
| 下一轮最小任务占位 | 3-B.4 | decision-fixed | not implemented | 推荐转 detector 设计轮 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | 待下一轮 |
| detector 问题范围定义 | 3-B.5 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | detector 设计轮测试规划 |
| detector 输入/输出契约边界 | 3-B.5 | decision-fixed | not implemented | 文档已固定 | 未暴露 | `source_engine.py` future hook / future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | detector skeleton 测试规划 |
| suspicious HTML candidate | 3-B.5 | decision-fixed | not implemented | documented only | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | heuristic 测试规划，仅文档建模 |
| challenge page candidate | 3-B.5 | decision-fixed | not implemented | candidate | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | future detector 静态分类测试规划 |
| gateway / WAF interception candidate | 3-B.5 | decision-fixed | not implemented | candidate | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | future detector 静态分类测试规划 |
| browser-required candidate signal | 3-B.5 | decision-fixed | not implemented | deferred to 3-D | 未暴露 | future `anti_bot_detector`, `browser_fallback_service` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | deferred |
| js-required candidate signal | 3-B.5 | decision-fixed | not implemented | deferred to 3-C | 未暴露 | future `anti_bot_detector`, `js_execution_sandbox` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | deferred |
| 下一轮最小 detector 任务占位 | 3-B.5 | decision-fixed | not implemented | 推荐转 3-B.6 detector skeleton 决策轮 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 待下一轮 |
| detector input contract | 3-B.6 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future `anti_bot_detector` input layer | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | detector input schema / fixture 测试规划 |
| detector output contract | 3-B.6 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future `anti_bot_detector` result layer | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | detector result mapping 测试规划 |
| challenge/gateway first-batch sample matrix | 3-B.6 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future detector sample fixtures | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | sample fixture / golden test 规划 |
| suspicious HTML sample inclusion decision | 3-B.6 | decision-fixed | not implemented | documented only | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | 暂不进入 first-batch 默认样本 |
| browser/js-required sample inclusion decision | 3-B.6 | decision-fixed | not implemented | deferred to 3-C / 3-D | 未暴露 | future `anti_bot_detector` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | 暂不进入 first-batch 默认样本 |
| challenge/gateway generic heuristic boundary | 3-B.6 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future `anti_bot_detector` heuristic layer | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | signal-bundle 测试规划 |
| 下一轮最小 detector 任务占位 | 3-B.6 | decision-fixed | not implemented | 推荐转 3-B.7 detector skeleton 实现轮 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 待下一轮 |
| detector input schema | 3-B.7 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_detector.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | `backend/tests/test_online_detector_skeleton.py` |
| detector output schema / classification result | 3-B.7 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/schemas/online_detector.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_detector_skeleton.py` |
| detector first-batch sample fixtures | 3-B.7 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/tests/fixtures/online_detector_samples.json` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_TRACEABILITY_INDEX.md` | `backend/tests/test_online_detector_skeleton.py` |
| detector static classification skeleton | 3-B.7 | implemented | 部分验证 | 未正式支持 | 未暴露 | `backend/app/services/online/detector_skeleton.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | `backend/tests/test_online_detector_skeleton.py` |
| live runtime 零接入边界 | 3-B.7 | implemented | 部分验证 | 文档已固定 | 未暴露 | `backend/app/services/online/fetch_service.py`, `backend/app/services/online/source_engine.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | `backend/tests/test_online_detector_skeleton.py`, 既有 online/import 回归 |
| 下一轮最小 detector 任务占位 | 3-B.7 | decision-fixed | not implemented | 推荐转 3-B.8 detector live 接缝决策轮 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 待下一轮 |
| detector live 输入来源决策 | 3-B.8 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future live seam adapter / coordinator | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | live seam contract 测试规划 |
| detector live hook 位置决策 | 3-B.8 | decision-fixed | not implemented | 文档已固定 | 未暴露 | `source_engine.py` seam + future thin coordinator | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | live seam integration 测试规划 |
| fetch early-raise 兼容策略 | 3-B.8 | decision-fixed | not implemented | 文档已固定 | 未暴露 | future exception-to-summary / fetch-outcome adapter | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | error-outcome seam 测试规划 |
| challenge/gateway 错误码 runtime 升级条件 | 3-B.8 | decision-fixed | not implemented | 文档已固定 | 未暴露 | 文档层 gate，future live detector path | `LEGADO_PHASE3_ERROR_CODES.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 正负样本 + live seam 回归规划 |
| 下一轮最小 detector 任务占位 | 3-B.8 | decision-fixed | not implemented | 推荐转 3-B.9 detector live seam skeleton 决策轮 | 未暴露 | 待定 | `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3B_REQUEST_RUNTIME.md` | 待下一轮 |
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
| L3-G | generic response_guard | implemented (timeout/429 only) | `backend/app/services/online/response_guard_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_response_guard.py` |
| L3-D | detector / anti-bot classification | decision-fixed / not implemented | future `anti_bot_detector` via `source_engine.py` seam | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3_ERROR_CODES.md` | challenge/gateway/browser/js-required detector 测试规划 |
| L3-D.1 | detector static skeleton contracts | decision-fixed / not implemented | future detector input/result contract layer | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | contract / fixture / golden test 规划 |
| L3-D.2 | detector offline static skeleton | implemented (offline only) | `backend/app/schemas/online_detector.py`, `backend/app/services/online/detector_skeleton.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md` | `backend/tests/test_online_detector_skeleton.py` |
| L3-D.3 | detector live seam decision | decision-fixed / not implemented | future `source_engine.py` seam + thin coordinator / fetch-outcome adapter | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_IMPLEMENTATION_PLAN.md`, `LEGADO_PHASE3_ERROR_CODES.md` | live seam contract / no-regression 测试规划 |
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
| response_guard | `backend/app/services/online/response_guard_service.py`, `backend/app/services/online/fetch_service.py` | `LEGADO_PHASE3B_REQUEST_RUNTIME.md`, `LEGADO_PHASE3_ERROR_CODES.md` | `backend/tests/test_online_response_guard.py` | implemented / partial validation / generic timeout-429 only |
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
| response guard | implemented / generic timeout-429 only |
| empty response classification | on hold / not implemented |
| content-type mismatch classification | narrow candidate / not implemented |
| detector scope | decision-fixed / not implemented |
| detector input contract | decision-fixed / not implemented |
| detector output contract | decision-fixed / not implemented |
| challenge/gateway first-batch sample matrix | decision-fixed / not implemented |
| challenge/gateway generic heuristic boundary | decision-fixed / not implemented |
| detector input schema | implemented / offline only |
| detector output schema | implemented / offline only |
| detector sample fixtures | implemented / offline only |
| detector static skeleton | implemented / offline only |
| detector live seam | decision-fixed / not implemented |
| detector error-code runtime upgrade gate | decision-fixed / not implemented |
| challenge / gateway detector candidates | skeleton-modeled / offline only |
| suspicious HTML detector candidate | documented only / not implemented |
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

当前 3-B.3 最小 generic response_guard 实装的最小验收链为：

1. `response_guard_service` 已存在
2. timeout classification 已存在
3. HTTP 429 classification 已存在
4. 2 个错误码已进入实现：
   - `LEGADO_REQUEST_TIMEOUT`
   - `LEGADO_RATE_LIMITED`
5. `backend/tests/test_online_response_guard.py` 已覆盖最小 generic classification 场景
6. 3-B.2 preflight、runtime skeleton、discovery、online books、online sources、importer 回归继续通过
7. `anti_bot_detector / suspicious HTML / challenge / 3-C / 3-D` 仍未进入实现

当前 3-B.4 决策轮的最小验收链为：

1. response_guard 当前边界已被重新核查
2. empty response 已明确为：
   - 暂缓
   - not implemented
3. content-type mismatch 已明确为：
   - 极窄候选
   - 当前不进入实现
4. response_guard / anti_bot_detector 的文档边界已再次固定
5. 下一轮最小任务已明确收敛为：
   - 优先进入 detector 设计轮
6. 本轮修改范围仅限文档，不触碰运行时代码路径

当前 3-B.5 detector / anti-bot 边界设计轮的最小验收链为：

1. `response_guard` 的已实现范围仍明确只到：
   - timeout
   - HTTP 429
2. detector 的问题范围已固定为：
   - body meaning / HTML semantics / challenge / gateway / browser-js-required hints
3. detector 的职责已固定为：
   - classification only
   - no bypass
   - no recovery orchestration
4. detector 的未来接缝已固定为：
   - `fetch_stage_response(...)` 之后
   - `parse_*_preview(...)` 之前
5. detector 候选能力状态已固定为：
   - challenge / gateway -> candidate
   - suspicious HTML -> documented only
   - js-required -> deferred to 3-C
   - browser-required -> deferred to 3-D
6. 下一轮最小任务已明确收敛为：
   - `Phase 3-B.6` detector skeleton 决策轮
7. 本轮仍然只修改文档，不触碰运行时代码路径

当前 3-B.6 detector 最小静态分类骨架决策轮的最小验收链为：

1. detector 输入契约已固定为：
   - stage context + bounded response evidence summary
   - 不直接绑定完整 `httpx.Response`
2. detector 输出契约已固定为：
   - structured classification result
   - 再映射错误码
3. first-batch 正向样本范围已固定为：
   - challenge
   - gateway
4. suspicious HTML 已明确：
   - documented only
   - 暂不进入 first-batch 默认样本
5. browser/js-required 已明确：
   - deferred
   - 暂不进入 first-batch 默认样本
6. challenge/gateway 的第一轮 heuristic 已固定为：
   - 极少数 generic signal bundles
   - 不允许 site-specific patterns 进入首轮边界
7. 下一轮最小任务已明确收敛为：
   - `Phase 3-B.7` detector skeleton 实现轮
8. 本轮仍然只修改文档，不触碰运行时代码路径

当前 3-B.7 detector 最小静态分类骨架实现的最小验收链为：

1. `backend/app/schemas/online_detector.py` 已存在
2. `backend/app/services/online/detector_skeleton.py` 已存在
3. `backend/tests/fixtures/online_detector_samples.json` 已存在
4. `backend/tests/test_online_detector_skeleton.py` 已覆盖：
   - input schema
   - output schema
   - sample fixtures
   - challenge/gateway 命中
   - 负样本 no_match
   - live runtime 零接入边界
5. detector 当前仍然只在离线静态骨架层工作
6. `fetch_service.py` / `source_engine.py` 没有接入 detector live path
7. 3-B.2 / 3-B.3 与 online/import 回归继续通过
8. 下一轮最小任务已明确收敛为：
   - `Phase 3-B.8` detector live 接缝决策轮

当前 3-B.8 detector live 接缝决策轮的最小验收链为：

1. 已再次核查：
   - `fetch_service.py`
   - `response_guard_service.py`
   - `source_engine.py`
   - `detector_skeleton.py`
   - `parser_engine.py`
   - `content_parse_service.py`
2. live detector 输入来源方向已固定为：
   - normalized `DetectorInput`
   - 由 future thin adapter / coordinator 单点构造
3. live hook 逻辑接缝已固定为：
   - `source_engine.py` 所在的 fetch -> parser seam
   - 而不是直接塞进 `fetch_service.py` 或 parser
4. 已明确确认：
   - `fetch_service.py` 的 `status_code >= 400` 早抛错会阻断一部分 future challenge/gateway live classification
5. future 兼容方向已固定为：
   - exception-to-summary / fetch-outcome adapter
   - 当前不进入 transport envelope 实装
6. `LEGADO_ANTI_BOT_CHALLENGE` / `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY` 的 `runtime-implemented` 升级门槛已固定
7. 本轮仍然只修改文档，不触碰任何 live runtime 代码路径
8. 下一轮最小任务已明确收敛为：
   - `Phase 3-B.9` detector live seam skeleton 决策轮
