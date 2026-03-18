# Legado Phase 3-B.1 Decisions

## 1. 文档定位

本文档用于固定 **Phase 3-B.1 实装前决策轮** 的四个关键结构决策。

当前结论必须始终理解为：

- 当前仓库仍停留在 `Phase 3-B` 的决策/设计阶段
- 本轮目标是把关键结构做小、做稳、做清楚
- 本轮默认只落文档，不进入 3-B 实装
- 本轮没有证据表明必须修改 router / importer / 数据库 / 前端 / 主流程代码

## 2. 决策轮扫描结论

### 2.1 当前仓库在 3-B 上真实已知的程度

结合当前文档、schema、service、router 与测试，仓库的 3-B 基线可以被准确描述为：

- `OnlineRequestDefinition` 仍只有：
  - `method`
  - `url`
  - `response_type`
  - `headers: dict[str, str]`
  - `query: dict[str, str]`
  - `body: dict[str, str]`
- `source_engine.py` 已负责：
  - stage request 渲染
  - 基础占位符替换
  - `request_profile_service -> fetch_service` 的调用接缝
- `request_profile_service.py` 当前只覆盖：
  - 最小 auth config 校验
  - session 必需/过期校验
  - headers/query/body 归一化
  - cookies 提取
- `fetch_service.py` 当前只覆盖：
  - `params=query`
  - `data=body`
  - timeout / invalid URL / status / response type 基础报错
- 当前并不存在：
  - 显式 `body_mode` enum
  - header template schema
  - signature placeholder schema
  - `response_guard`
  - `anti_bot_detector`
  - 稳定的 3-B 首批错误码落地策略

因此，当前仓库只具备：

- 隐式 `query`
- 隐式 `form`
- 简单 header/query/body 字符串占位替换
- Session/Cookie skeleton hook

还不具备：

- 复杂请求描述的稳定 schema
- 响应分类层
- anti-bot detection 层
- JS / browser 依赖能力

### 2.2 为什么本轮要先做决策，而不是直接实装

当前最危险的问题不是“没有代码”，而是“结构含义还没钉死”：

- `body` 现在既像“form body”，又没有显式 mode，继续写代码会把语义散落到 `schema / request_profile / fetch_service`
- `source_engine` 已经支持简单占位替换，如果不先区分“静态占位”和“未来签名占位”，很容易把“可建模”误写成“可执行”
- `fetch_service` 当前只有传输逻辑；如果不先决定 `response_guard` 和 `anti_bot_detector` 的边界，3-B 实装极易把风险分类、内容解析、anti-bot 检测混写到一起
- 3-B 错误码现在既有“已在 enum 预留”的，也有“只在文档中建模”的；不先决定首批错误码，下一轮容易写出难以测试、难以回退的半成品

### 2.3 当前最危险的设计歧义点

本轮最需要收敛的四个歧义点正是：

1. `body mode` 到底是公共 source schema、内部 descriptor，还是 fetch 层行为
2. `header template` 和 `signature placeholder` 是“静态描述”还是“可执行模板”
3. `response_guard` 和 `anti_bot_detector` 是一层还是两层
4. 哪些错误码值得先入代码，哪些继续只留在文档

### 2.4 本轮是否需要落代码

#### Step 1：只做文档与决策是否已经足够

结论：**足够。**

原因：

- 当前仓库已经暴露了足够清晰的接缝：
  - `source_engine`
  - `request_profile_service`
  - `fetch_service`
- 当前缺的是“稳定决策”，不是“更多骨架代码”
- 本轮四个问题都可以仅凭现有代码与文档得到稳定结论

#### Step 2：是否存在必须落代码的充分证明

结论：**不存在。**

原因：

- 不落代码并不会阻塞下一轮
- 下一轮真正最小可做的一步，仍然可以在这些决策固定后再做
- 本轮若硬加 enum/type/schema，也会立刻遇到“该挂在哪层”的同一问题

因此本轮默认停在文档层。

## 3. 决策 1：`request body mode` 放在哪层

### 3.1 当前证据

当前项目已经隐含支持了 `body mode` 的一部分能力：

- `query`
  - 已通过 `request.query` + `httpx.request(..., params=query)` 隐式支持
- `form`
  - 已通过 `request.body` + `httpx.request(..., data=body)` 隐式支持

当前缺口在于：

- 没有显式 enum
- `json` / `raw` 没有表达位
- `body` 当前总被解释为 `dict[str, str]`
- fetch 层只知道 `data=body`，不知道 `json` / `content`

### 3.2 方案 A：直接放进 `OnlineRequestDefinition`

- 优点
  - source schema 直接表达完整能力
  - manual source/create/update 看起来最直观
- 缺点
  - 直接扩大公共 router/schema 契约
  - 会逼 `online_sources.py` / `source_validator.py` / importer 一起感知新语义
  - 很容易让“文档设计”被误读成“公共接口已支持”
- 风险
  - 污染 router
  - 污染 importer 白名单边界
  - 让 Phase 1/2 稳定 contract 提前发生 schema 演进
- 对现有项目侵入性
  - 高
- 是否利于下一轮小步实装
  - 不利

### 3.3 方案 B：继续保持隐式，不新增显式 mode

- 优点
  - 零 schema 变更
  - 当前代码几乎不用动
- 缺点
  - 语义继续散落在 `source_engine / request_profile_service / fetch_service`
  - `json` / `raw` 永远没有稳定表达位
  - 测试和错误码无法精确绑定到 mode
- 风险
  - 后续每新增一种 body 行为，都要继续在多层补特判
  - 更容易出现“部分支持但无明确边界”
- 对现有项目侵入性
  - 低
- 是否利于下一轮小步实装
  - 不利

### 3.4 方案 C：在内部 `request descriptor` 中定义显式 enum，由 `request_runtime_schema` 承载

- 优点
  - 可以把“请求描述”与“最终 transport profile”拆开
  - 不改 public source schema，也不改 importer
  - 适合后续小步引入 `request_body_encoder`
  - 能保证 `body_mode` 只在一个内部层次定义一次
- 缺点
  - 需要承认当前项目会出现“public schema 仍旧简单、internal descriptor 更丰富”的双层结构
  - 初期文档心智成本略高
- 风险
  - 如果命名不清晰，可能和 `RequestProfile` 混淆
- 对现有项目侵入性
  - 低到中
- 是否利于下一轮小步实装
  - 最有利

### 3.5 推荐方案

推荐：**方案 C**

### 3.6 不推荐另外两种方案的原因

- 不选方案 A
  - 当前阶段最重要的是不污染 router / importer
  - 把 `body_mode` 直接塞进 `OnlineRequestDefinition`，会让 Phase 3-B 设计变成公共 schema 扩张
- 不选方案 B
  - 继续隐式会让下一轮实现没有稳定落点
  - 这正是本轮要解决的结构歧义

### 3.7 固定结论

1. 当前项目已经隐含支持：
   - `query`
   - `form`
2. 应引入显式 enum：
   - `query`
   - `form`
   - `json`
   - `raw`
3. 第一批真正允许进入实现的 mode 只建议开放：
   - `query`
   - `form`
4. `json` / `raw` 本轮只固定名称与语义，不激活
5. `body_mode` 应挂在：
   - 内部 `request descriptor`
   - 其 schema 归属 `request_runtime_schema`
6. `RequestProfile` 只保留“最终 transport-ready 结果”，不作为 mode 的单一事实来源
7. `fetch_service` 不持有 mode 决策，只消费编码后的结果
8. 避免散落的规则是：
   - 只允许一个内部字段叫 `body_mode`
   - source definition 不直接新增该字段
   - importer 不接收该字段
   - router 不暴露该字段

## 4. 决策 2：`header template / signature placeholder` 放在哪层

### 4.1 当前证据

当前项目已经部分存在“header template 的影子”：

- `source_engine._render_mapping()` 会对 headers/query/body 做统一字符串占位替换
- `source_validator.py` 允许有限 placeholder：
  - `keyword`
  - `page`
  - `detail_url`
  - `catalog_url`
  - `chapter_url`
- `source_validator.py` 同时禁止：
  - `Authorization`
  - `Cookie`
  - `login`
  - `session`
  - `webview`
  - `requests/steps/pipeline`

这意味着：

- 当前只支持“简单 runtime placeholder 替换”
- 不支持“签名模板”
- 不支持“浏览器态 header”
- 不支持“可执行模板”

### 4.2 方案 A：把 `header template` 直接做成 `request profile` 的一部分

- 优点
  - 数据结构最少
  - 看起来离 fetch 最近
- 缺点
  - `RequestProfile` 会同时承担“待解析模板”和“最终请求”两种语义
  - 很容易让模板存在被误解成模板可执行
- 风险
  - `RequestProfile` 语义膨胀
  - fetch 前后的边界变模糊
- 对现有项目侵入性
  - 中
- 是否利于下一轮小步实装
  - 一般

### 4.3 方案 B：单独创建独立 `request_template_resolver`

- 优点
  - 分层最干净
  - 未来扩展 header/query/body 模板统一解析时很好用
- 缺点
  - 对当前阶段偏重
  - 容易在还没确定模板范围前就过度模块化
- 风险
  - 下一轮最小实装会被迫先做 resolver，再做真正业务边界
- 对现有项目侵入性
  - 中到高
- 是否利于下一轮小步实装
  - 不够利于

### 4.4 方案 C：模板归属内部 `request descriptor`，解析先收敛在 `request_profile_service` 内部 helper

- 优点
  - 模板仍然属于“请求描述层”，和 body mode 在同一层建模
  - 解析逻辑先收敛在已有 `request_profile_service`，不额外拉新 service
  - 若未来模板范围扩大，再从 helper 提炼独立 resolver 也不晚
- 缺点
  - 需要文档清楚说明“属于 descriptor，不等于当前可执行”
- 风险
  - 如果 helper 和真正 resolver 的升级路径不写清楚，后续可能重复搬迁
- 对现有项目侵入性
  - 低
- 是否利于下一轮小步实装
  - 最利于

### 4.5 推荐方案

推荐：**方案 C**

### 4.6 不推荐另外两种方案的原因

- 不选方案 A
  - 会混淆“待解析模板”和“最终请求画像”
- 不选方案 B
  - 当前只有 header template / signature placeholder 需要固定边界，单独拆 resolver 过重

### 4.7 固定结论

1. header template 本质上属于：
   - **请求描述层**
2. 它应与 body mode：
   - 在同一内部 `request descriptor` / `request_runtime_schema` 层建模
3. signature placeholder 当前只允许：
   - **占位建模**
   - **能力标记**
   - **错误分类**
4. signature placeholder 当前明确不允许：
   - 真实求值
   - 自动签名生成
   - JS 求值
   - 浏览器态兜底
5. 可视为静态安全配置的 header 仅限：
   - 固定字面量 `Accept`
   - 固定字面量 `Accept-Language`
   - 固定字面量 `Referer`
   - 固定字面量 `Origin`
   - 固定字面量 `User-Agent`
   - 固定字面量 `Content-Type`
   - 固定字面量普通 `X-*` 头
6. 一旦出现以下类别，应标记为未来能力，而不是当前可执行：
   - `Authorization`
   - `Cookie`
   - session/token 相关头
   - `X-Sign` / `X-Signature`
   - `X-Timestamp`
   - `X-Nonce`
   - `sec-ch-*`
   - 明显依赖浏览器指纹或挑战页状态的头
7. 这些 future header/placeholder 应使用能力标签区分：
   - `requires_signature_engine`
   - `requires_js`
   - `requires_browser`
8. 当前不单独创建 `request_template_resolver`
9. 下一轮若只做最小实装，模板解析先留在：
   - `request_profile_service` 内部 helper
10. 为避免“模板存在 = 模板已可执行”的误解，文档必须始终写成：
    - `template-modeled`
    - `not executable in 3-B.1`
    - `classification only`

## 5. 决策 3：`response_guard` 与 `anti_bot_detector` 如何拆分

### 5.1 当前证据

当前响应相关行为全部集中在 `fetch_service.py`：

- timeout -> 通用文本错误
- invalid URL -> 通用文本错误
- HTTP status >= 400 -> 通用文本错误
- content-type mismatch -> 通用文本错误
- response size limit -> 通用文本错误

当前不存在：

- response classification 层
- anti-bot detection 层

### 5.2 方案 A：合并成一个统一 `response_runtime_service`

- 优点
  - 概念最少
  - 首看上去实现简单
- 缺点
  - generic response guard 和 anti-bot heuristic 容易混成一团
  - 后续最容易把 bypass/retry 也偷偷塞进来
- 风险
  - 模块语义失真
  - 错误码归因模糊
  - anti-bot 逻辑污染普通 HTTP 主链
- 对现有项目侵入性
  - 中
- 是否利于下一轮小步实装
  - 短期看似利，长期最危险

### 5.3 方案 B：保留两层，先 `response_guard`，后 `anti_bot_detector`

- 优点
  - `response_guard` 只处理 generic 合法性与基础分类
  - `anti_bot_detector` 只处理 challenge/gateway/suspicious HTML 检测
  - 更容易把“识别”与“绕过”彻底拆开
- 缺点
  - 多一个模块边界需要文档约束
- 风险
  - 如果调用顺序不清楚，可能重复分类
- 对现有项目侵入性
  - 低到中
- 是否利于下一轮小步实装
  - 最利于

### 5.4 方案 C：继续全留在 `fetch_service`

- 优点
  - 最省代码
- 缺点
  - 会把 L0 传输层写成 L3 运行时分类层
  - 以后最难回退
- 风险
  - `fetch_service` 职责被彻底污染
  - parser/content_parse 前的边界不再清晰
- 对现有项目侵入性
  - 低
- 是否利于下一轮小步实装
  - 不利

### 5.5 推荐方案

推荐：**方案 B**

### 5.6 不推荐另外两种方案的原因

- 不选方案 A
  - 会把 generic guard 与 anti-bot heuristic 混为一谈
- 不选方案 C
  - 会直接污染 `fetch_service`

### 5.7 固定边界

#### 属于 `response_guard` 的检查

- transport timeout 的稳定错误码映射
- HTTP status 的基础分类
- `429` / 明确限流响应分类
- redirect policy 违规
- response size / empty body / malformed JSON 这类基础合法性检查
- content-type mismatch 的 generic 分类

#### 属于 `anti_bot_detector` 的分类

- challenge 页面识别
- anti-bot gateway / WAF block 页面识别
- suspicious HTML 识别
- “需要 JS” 的内容级信号识别
- “需要浏览器态” 的内容级信号识别

#### 不应归入 `anti_bot_detector` 的内容

- timeout
- 普通 4xx/5xx
- 纯 transport 错误
- 未约定的 retry/backoff

#### `rate limit` 归属

`rate limit` 更适合先归入 `response_guard`，原因是：

- `429` 是稳定 HTTP 信号
- 可纯 HTTP 判定
- 不需要 anti-bot heuristic

### 5.8 只允许分类，不允许自动绕过

以下能力在 3-B 中只允许：

- classify
- label
- map error code
- stop execution

以下能力明确不允许：

- auto retry to success
- auto challenge bypass
- auto cookie refresh
- auto browser fallback
- auto JS signature generation
- auto recovery orchestration

### 5.9 与第一批错误码的映射关系

- 适合先从 `response_guard` 进入首批实现：
  - `LEGADO_REQUEST_RUNTIME_TIMEOUT`
  - `LEGADO_RATE_LIMITED`
- 暂不建议首批就从 `anti_bot_detector` 落代码：
  - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - `LEGADO_ANTI_BOT_CHALLENGE`
  - `LEGADO_SUSPICIOUS_HTML_RESPONSE`

原因：

- detector 侧还依赖更稳定的规则样本
- 这些分类更容易被误读为“已经具备绕过能力”

## 6. 决策 4：第一批真正允许入代码的 3-B 错误码

### 6.1 方案 A：首批就把 preflight + detector + 环境判断一起放进代码

- 优点
  - 看起来推进更快
  - 一次性覆盖范围更大
- 缺点
  - 首批就要同时面对 body mode、template、timeout、gateway、challenge、JS/browser-required 等多类问题
  - 很难保证每个错误码都可稳定复现
- 风险
  - detector 规则未冻结就入代码，容易误报
  - 容易把“分类存在”误读成“已具备绕过能力”
- 对现有项目侵入性
  - 高
- 是否利于下一轮小步实装
  - 不利

### 6.2 方案 B：首批只放“纯本地 preflight + 纯 HTTP 稳定分类”错误码

- 优点
  - 每个错误码都能稳定构造测试
  - 不依赖 JS / 浏览器 / captcha
  - 最适合做第一轮 3-B 小步实装
- 缺点
  - detector 类错误码要后置一轮
- 风险
  - 需要文档明确说明“首批不等于全部 3-B 错误码”
- 对现有项目侵入性
  - 低
- 是否利于下一轮小步实装
  - 最利于

### 6.3 方案 C：本轮继续把所有 3-B 错误码都停留在文档，不指定首批

- 优点
  - 最保守
  - 完全没有过早落代码风险
- 缺点
  - 下一轮没有清晰起步点
  - 3-B.1 决策轮的“为下一轮做小做稳”目标就没有真正完成
- 风险
  - 后续再次进入 3-B 时，还会回到同样的“先实现哪几个错误码”争论
- 对现有项目侵入性
  - 最低
- 是否利于下一轮小步实装
  - 不利

### 6.4 推荐方案

推荐：**方案 B**

### 6.5 不推荐另外两种方案的原因

- 不选方案 A
  - 首批范围过宽，无法保证“小步可回退”
- 不选方案 C
  - 决策轮如果不收敛首批错误码，下一轮仍然没有最小实现入口

### 6.6 首批错误码入代码标准

第一批 3-B 错误码只有同时满足以下条件，才值得进入代码：

1. 可由纯 HTTP 或纯本地 preflight 判定
2. 可稳定复现
3. 可写单元测试
4. 不依赖 JS / 浏览器 / 验证码
5. 不改变 router / importer / 数据库 / 前端公共语义
6. 对下一轮最小实装有直接支撑

### 6.7 第一批数量上限

推荐控制在：**5 个以内**

原因：

- 3-B 首轮实现应先做“窄而稳”的验证点
- 错误码一多，往往意味着模块边界还没收紧

### 6.8 推荐首批候选

推荐首批候选为：

1. `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
   - 本地 preflight 可判定
   - 直接服务 body mode 决策
2. `LEGADO_INVALID_HEADER_TEMPLATE`
   - 本地 preflight 可判定
   - 直接服务 header template 决策
3. `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
   - 本地 preflight 可判定
   - 能明确表达“建模存在，不等于可执行”
4. `LEGADO_REQUEST_RUNTIME_TIMEOUT`
   - transport 层稳定可复现
   - 可直接 mock 超时
5. `LEGADO_RATE_LIMITED`
   - `429` 或稳定 header/body 信号可判定
   - 纯 HTTP，可测

### 6.9 虽然重要，但当前仍不建议进入首批代码

- `LEGADO_REQUEST_PROFILE_INVALID`
  - 过于宽泛，更适合作为文档 umbrella，不适合作为第一批真实落地入口
- `LEGADO_REQUEST_RETRY_EXHAUSTED`
  - 当前没有 retry 机制，先入代码会形成空壳语义
- `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
  - detector 规则尚未冻结
- `LEGADO_ANTI_BOT_CHALLENGE`
  - detector 规则尚未冻结
- `LEGADO_SUSPICIOUS_HTML_RESPONSE`
  - detector 规则尚未冻结，且最容易引发误报争议

### 6.10 必须延后到 3-C / 3-D 的错误码

- `LEGADO_JS_EXECUTION_REQUIRED`
  - 延后到 `3-C`
- `LEGADO_BROWSER_STATE_REQUIRED`
  - 延后到 `3-D`

### 6.11 推荐顺序

如果下一轮只做最小一步，推荐顺序是：

1. 先实现本地 preflight 类：
   - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
   - `LEGADO_INVALID_HEADER_TEMPLATE`
   - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
2. 再实现 generic HTTP 分类类：
   - `LEGADO_REQUEST_RUNTIME_TIMEOUT`
   - `LEGADO_RATE_LIMITED`
3. 最后再讨论 detector 类：
   - `LEGADO_BLOCKED_BY_ANTI_BOT_GATEWAY`
   - `LEGADO_ANTI_BOT_CHALLENGE`
   - `LEGADO_SUSPICIOUS_HTML_RESPONSE`

## 7. 下一步最小可执行任务

在本轮决策固定后，下一步最小可执行任务建议是：

- 仍然停留在 `Phase 3-B` 范围内
- 只做内部 `request_runtime_schema` / `request descriptor` 最小补充
- 只为以下三类错误码建立最小 preflight 校验与单测：
  - `LEGADO_UNSUPPORTED_REQUEST_BODY_MODE`
  - `LEGADO_INVALID_HEADER_TEMPLATE`
  - `LEGADO_UNSUPPORTED_SIGNATURE_FLOW`
- 不改 router
- 不改 importer
- 不改数据库
- 不改前端
- 不进入 retry / anti-bot detector / JS / browser fallback

## 8. 本轮阶段结论

本轮完成后，阶段状态应明确写成：

- 当前仍停留在 `Phase 3-B` 决策/设计阶段
- 当前 **没有** 进入 3-B 实装
- 当前 **没有** 进入 3-C / 3-D
- 当前最小下一步已经明确，但尚未执行
