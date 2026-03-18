# Legado Phase 3 Architecture

## 1. Phase 3 目标边界

Phase 3 的目标不是“直接做完高兼容运行时”，而是在 **不破坏现有本地 TXT 阅读能力、不破坏 Phase 1/Phase 2 既有链路** 的前提下，为后续高级兼容能力建立可控的运行时基础设施。

本轮只正式进入：

- `Phase 3-0`：项目扫描、架构设计、风险收口、文档落地
- `Phase 3-A`：Session / Cookie / 登录态基础设施的最小骨架

本轮明确 **不进入**：

- JS 引擎
- WebView / 浏览器渲染
- 自动登录编排
- 图形验证码
- 复杂反爬绕过
- 多请求链式运行时
- 完整 Cookie 持久化

## 1.1 当前限制

当前仓库对 Phase 3 的真实落地状态，必须被准确理解为：

- 当前只完成了 `Phase 3-0` 与 `Phase 3-A` 第一轮最小运行时骨架，以及本轮 `Phase 3-A.1` 收口
- 当前只是 `runtime skeleton`，不是“已正式支持登录型书源”
- 当前 session storage 是内存级实现，不是生产级持久化方案
- 进程重启后 session 会丢失
- 不保证多 worker / 多实例之间的一致性
- 不保证生产级用户隔离与跨进程共享
- 不提供自动登录流程
- 不提供验证码 / challenge 处理
- 不支持浏览器态认证
- 不支持 JS 驱动签名、动态计算或脚本式认证
- 不支持 Cookie 自动刷新
- 当前 importer 仍不直接接收 Cookie / 登录态 / JS / WebView 等高级能力字段

因此，当前阶段的正确表述应始终是：

> 已完成在线运行时骨架与注入扩展点，但尚未正式支持登录型书源。

## 2. 为什么不能直接做“高兼容运行时”

直接推进高兼容运行时会同时引入多类高风险变化：

- 运行时风险：会话态、Cookie、反爬、JS、浏览器态都不是静态 importer 问题，而是执行环境问题。
- 架构风险：当前在线链路已经与本地 TXT 链路解耦，但还没有独立的会话/认证运行层，直接硬塞会污染 `source_engine` 与 `fetch_service` 的职责。
- 回归风险：Phase 2 当前基线明确是 `50 passed` 所代表的静态 importer + discovery 回归链，不允许为了高级兼容破坏 `importer -> detail -> catalog -> chapter`。
- 维护风险：一旦把登录态、Cookie、JS、WebView 同时推进，就会让调试边界、错误归因、回退策略一起失控。

因此 Phase 3 必须拆成“先骨架、后能力”的多阶段推进，而不是一次性冲到高兼容。

## 3. 为什么本轮只进入 3-0 + 3-A

当前项目已经具备：

- 在线书源定义、校验、静态 importer
- 在线 discovery 的单请求执行链
- 在线书籍入书架、目录缓存、正文缓存、在线阅读进度
- 前端对本地/在线书籍共存的统一展示与阅读分发

但当前项目还不具备：

- 会话上下文 schema
- Cookie/session 生命周期管理
- 认证配置结构
- 请求执行层的会话注入钩子
- 高风险能力的错误码分层

因此本轮最合理的推进顺序是：

1. 先把现有执行链扫描清楚
2. 再定义 Phase 3 文档、模块边界和错误码分层
3. 最后仅在在线请求执行链增加“可选 session 注入点”和“最小 session storage abstraction”

## 4. 与 Phase 1 / Phase 2 的关系

### 4.1 Phase 1

Phase 1 提供了在线阅读的最小可运行链路：

- `online_sources`
- `source_normalizer`
- `source_validator`
- `source_engine`
- `fetch_service`
- `parser_engine`
- `content_parse_service`

Phase 3-A 不能重写这些链路，只能在它们之上增加扩展点。

### 4.2 Phase 2

Phase 2 的定位仍然是：

- 严格白名单静态 importer
- 静态字段映射
- 静态 alias / parser 归一化
- `importer -> detail -> catalog -> chapter` 回归链

Phase 3-A 不得把 Cookie / 登录态 / Session 直接混入 Phase 2 importer 白名单，也不得倒逼 Phase 2 接受高风险字段。

换句话说：

- `Phase 2` 继续负责“能不能导入、能不能静态映射”
- `Phase 3` 才开始负责“未来如何安全执行需要会话态的书源”

## 5. 项目扫描结论

### 5.1 可复用模块

后端可复用：

- `backend/app/services/online/source_engine.py`
  - 已承担在线 discovery 的阶段编排，适合作为会话注入点的上层入口。
- `backend/app/services/online/fetch_service.py`
  - 已承担真实 HTTP 请求执行，适合作为 cookies / auth headers 的最小注入点。
- `backend/app/services/online/source_normalizer.py`
  - 已承担在线书源定义归一化，可为后续 auth config 持久化接入提供位置。
- `backend/app/services/online/source_validator.py`
  - 继续负责 Phase 1/2 的静态校验边界，本轮不直接扩展为高兼容运行时校验器。
- `backend/app/services/online/online_sources.py`
  - 已负责在线书源存储与序列化，可作为未来 auth runtime 持久化的外层服务入口。
- `backend/app/services/online/online_books.py`
  - 已负责在线书籍入架、目录缓存、正文缓存；未来登录型书源可复用这一链路。
- `backend/app/services/online/online_progress.py`
  - 已与本地进度链路保持同构，说明在线/本地阅读边界已经比较稳定。
- `backend/app/services/library.py`
  - 已把本地书籍与在线书籍聚合到统一书架视图，无需为 Phase 3 重写书架聚合层。

前端可复用：

- `frontend/src/api/library.ts`
- `frontend/src/composables/useBookDetailSource.ts`
- `frontend/src/composables/useReaderSource.ts`
- `frontend/src/pages/BookshelfPage.vue`
- `frontend/src/pages/BookDetailPage.vue`
- `frontend/src/pages/ReaderPage.vue`

这些模块已经通过 `libraryBookId` 将本地 / 在线阅读分流，Phase 3-A 不需要大改前端结构。

### 5.2 必改模块

- `backend/app/services/online/fetch_service.py`
  - 需要增加 cookies 注入能力，但必须保持默认行为不变。
- `backend/app/services/online/source_engine.py`
  - 需要增加 request profile / session context 的可选扩展点。

### 5.3 建议新增模块

本轮落地：

- `session_context_schema` / `auth_runtime_schema`
  - 以独立 schema 文件落地，避免污染 Phase 2 importer schema。
- `session_handler`
  - 负责 session storage abstraction 与 context 解析。
- `request_profile_service`
  - 负责把 stage request 与 session/auth runtime 合并成最终请求画像。

本轮只设计、不实现：

- `auth_flow_service`
- `anti_bot_handler`
- `js_execution_sandbox`
- `browser_fallback_service`

### 5.4 风险点

- 如果把 session 注入放进本地 TXT 链路，会直接破坏架构边界。
- 如果修改 `online_source` 的现有 schema 契约过大，会影响 Phase 1/2 已有接口与测试。
- 如果一开始就落数据库持久化，会引入迁移策略、数据清理和安全存储问题。
- 如果 importer 过早接受登录态字段，会造成“已导入但不可执行”的灰区增大。

### 5.5 暂缓项

- Cookie 持久化数据库模型
- 完整登录表单编排
- 多账户 / 多会话管理
- 验证码、挑战页、反爬绕过
- JS 沙箱
- 浏览器态 / WebView 兜底

## 6. Phase 3 模块层次

建议按以下层次扩展，而不是把新能力直接堆进 `fetch_service`：

### 6.1 Schema 层

- `session_context_schema`
- `auth_runtime_schema`
- `runtime error code schema`

职责：

- 统一描述 session、cookie、auth config、request profile 的结构
- 为后续前后端对接、错误码、traceability 提供稳定契约

### 6.2 Session 运行层

- `session_handler`
- `session storage abstraction`

职责：

- 保存 / 读取 / 清理 session context
- 当前阶段仅提供内存实现，避免 DB 迁移

### 6.3 Request 装配层

- `request_profile_service`

职责：

- 接收原始 stage request
- 合并 session headers / cookies
- 校验 auth config 与 session 状态
- 输出最终请求画像

### 6.4 HTTP 执行层

- `fetch_service`

职责：

- 只负责执行最终请求画像
- 不负责理解登录流程
- 不负责理解反爬策略

### 6.5 更高风险能力层

- `auth_flow_service`
- `anti_bot_handler`
- `js_execution_sandbox`
- `browser_fallback_service`

这些模块在 3-B / 3-C / 3-D 再逐步引入。

## 7. Phase 3-A 最小实现策略

本轮代码只做以下几件事：

1. 定义 `SessionContext` / `SessionCookie` / `OnlineAuthConfig` / `RequestProfile`
2. 定义 Phase 3 运行时错误码枚举
3. 实现 in-memory session storage abstraction
4. 实现 `request_profile_service`
5. 在 `source_engine -> fetch_service` 增加可选 session 注入点
6. 增加最小测试骨架，确保：
   - 无 session 时旧链路语义不变
   - 有 session 时可以注入 headers / cookies
   - 缺失/过期 session 时能给出稳定错误码

### 7.1 Phase 3-A.1 收口结论

本轮 `Phase 3-A.1` 的目标不是增加新能力，而是收紧上一轮骨架的边界表达与保护：

- 核查 `source_engine` / `fetch_service` 的可选 runtime 参数仍保持默认兼容
- 确认 router / API 层没有被强制感知 `auth_config` / `session_context`
- 为 session handler 补充“过期过滤、用户/书源匹配、clear/overwrite”级别的保护性行为
- 为 request injection 补充“空值不污染旧请求”的保护
- 统一文档口径为“已骨架化、部分验证、未正式支持、非生产就绪”

本轮完成后，Phase 3 仍然 **没有** 进入：

- 登录型书源正式支持
- Cookie 生命周期管理
- 自动登录编排
- 复杂反爬
- JS / 浏览器态

## 8. 回退策略

本轮回退策略必须简单明确：

- 不引入数据库表
- 不改现有在线书源持久化结构
- 不改本地 TXT 阅读模型
- 会话注入为可选参数，不传时保持现有逻辑

因此如果 Phase 3-A 出现问题，回退只需要移除：

- `source_engine` 中的 request profile 装配调用
- `fetch_service` 中新增的 cookies 参数支持
- 新增 runtime schema / service 文件

不会影响现有书架、阅读页、在线 discovery 或本地 TXT 主链。
