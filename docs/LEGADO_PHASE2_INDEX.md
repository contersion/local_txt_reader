# Legado Phase 2 文档总览

本文档是当前项目 **Phase 2：Legado 静态 importer 第一阶段** 的总入口，用于说明：

- 当前 Phase 2 做到了什么
- 当前 Phase 2 明确不做什么
- 各文档分别负责什么
- 当你要新增字段、扩 alias、补样本、查错误码时，应该先看哪份文档

当前阶段性结论以以下文档为准：

- [LEGADO_PHASE2_STATUS.md](./LEGADO_PHASE2_STATUS.md)
- [LEGADO_PHASE2_ACCEPTANCE.md](./LEGADO_PHASE2_ACCEPTANCE.md)

## 冻结基线

当前 Phase 2 文档按以下基线冻结维护：

- 文档基线日期：`2026-03-18`
- 阶段结论：`Phase 2 完成`
- 当前定位：`Legado 静态 importer 第一阶段`
- 测试基线：`50 passed`
- 样本基线：`S1-S29`
- 错误码基线：`21 个错误/警告码`

当前阶段仅允许以下维护性增量继续落在 Phase 2 范围内：

- 小范围静态 alias 增量
- 小范围静态字段增量
- 文档、测试、样本维护

以下能力不得混入当前冻结范围；如需推进，必须单独进入后续阶段讨论：

- JS
- Cookie / 登录态
- WebView
- 高兼容运行时

除上述维护性增量外，当前 Phase 2 应视为已冻结的静态 importer 文档基线，不再在本阶段内扩展新的运行时能力。

## 1. 当前阶段定位

当前 Phase 2 的目标不是“高兼容 Legado 运行时”，而是：

- 严格白名单导入
- 静态字段映射
- 静态 alias 归一化
- 静态 parser 归一化
- 明确错误码
- 明确样本覆盖
- 导入成功后继续复用现有 Phase 1 执行链

换句话说，当前 Phase 2 是：

> **静态 importer 第一阶段**

而不是：

- JS 执行器
- Cookie / 登录态兼容层
- WebView 抓取层
- 多请求链式编排层
- 高兼容运行时

## 2. 当前已完成能力

当前 Phase 2 已完成：

- 严格白名单 importer
- `Legado -> OnlineSourceDefinition` 静态映射
- 稳定错误码体系
- dry-run 校验
- 导入并落库
- alias 映射增强
- CSS / JSoup 静态归一化增强
- importer 结构化 issue 输出
- 最小样本矩阵
- Traceability 索引
- importer 回归测试
- 9 个补齐错误码的样例/Traceability/自动化测试闭环
- import 后 `detail -> catalog -> chapter` 正式回归
- 与现有 discovery 执行链兼容

## 3. 当前明确不做的能力

以下能力 **不属于当前 Phase 2**：

- JS / `@js:` / `<js>`
- Cookie
- Authorization
- 登录态
- session / token 刷新
- WebView
- proxy
- 多请求链
- 复杂变量系统
- 条件 DSL
- replace / 净化 DSL
- 高兼容运行时

如果后续要做这些，必须单独升级阶段讨论，不能偷偷塞进当前 importer。

## 4. 文档导航

### 4.1 字段映射规范

文件：
- [LEGADO_FIELD_MAPPING_PHASE2.md](./LEGADO_FIELD_MAPPING_PHASE2.md)

用途：
- 定义当前支持哪些字段
- 定义字段如何映射到 canonical `OnlineSourceDefinition`
- 定义哪些字段必须拒绝
- 定义哪些字段允许 `warning + ignore`

适合什么时候看：
- 想知道某个 Legado 字段支不支持
- 想知道某个 alias 会映射到哪里
- 想新增字段映射前先确认边界

### 4.2 错误码规范

文件：
- [LEGADO_IMPORT_ERROR_CODES.md](./LEGADO_IMPORT_ERROR_CODES.md)

用途：
- 定义 importer / validator 的错误码
- 定义 fatal / warning 语义
- 定义常见失败类型

适合什么时候看：
- 想知道某类导入失败应该报什么错
- 想补错误码文档
- 想统一前后端错误展示

### 4.3 最小样本矩阵

文件：
- [LEGADO_IMPORT_SAMPLE_MATRIX.md](./LEGADO_IMPORT_SAMPLE_MATRIX.md)

用途：
- 定义当前 importer 的最小样本集
- 固定 success / warning / reject 样本
- 说明每类样本分别覆盖什么能力

适合什么时候看：
- 想知道当前 importer 是靠哪些样本固定住的
- 想补一个新的独立样本
- 想判断某类能力目前有没有样本覆盖

### 4.4 Traceability 索引

文件：
- [LEGADO_IMPORT_TRACEABILITY_INDEX.md](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)

用途：
- 把字段、样本、测试函数、错误码串起来
- 建立“字段 -> 样本 -> 测试 -> 错误码”的追溯链

适合什么时候看：
- 想知道某个字段由哪个样本覆盖
- 想知道某个样本对应哪个测试函数
- 想知道某个 reject / warning 对应哪个错误码

### 4.5 Issue 结构规范

文件：
- [LEGADO_IMPORT_ISSUE_SCHEMA.md](./LEGADO_IMPORT_ISSUE_SCHEMA.md)

用途：
- 定义 `errors[] / warnings[]` 的结构
- 说明：
  - `error_code`
  - `severity`
  - `source_path`
  - `stage`
  - `field_name`
  - `raw_value`
  - `normalized_value`
- 说明向后兼容字段如何保留

适合什么时候看：
- 前端要接 importer 错误展示
- 想知道某条 issue 应该长什么样
- 想增强 issue 定位信息时

### 4.6 状态与验收

文件：
- [LEGADO_PHASE2_STATUS.md](./LEGADO_PHASE2_STATUS.md)
- [LEGADO_PHASE2_ACCEPTANCE.md](./LEGADO_PHASE2_ACCEPTANCE.md)

用途：
- 说明当前 Phase 2 的真实完成状态
- 固定最终验收证据与测试命令
- 区分“核心实现完成”和“阶段正式完成”

适合什么时候看：
- 想确认 Phase 2 现在能不能正式宣布完成
- 想看最终验收证据
- 想知道本阶段收尾时到底补齐了什么

## 5. 推荐阅读顺序

### 场景 A：我想知道某个字段支不支持

按这个顺序看：

1. [LEGADO_FIELD_MAPPING_PHASE2.md](./LEGADO_FIELD_MAPPING_PHASE2.md)
2. [LEGADO_IMPORT_TRACEABILITY_INDEX.md](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
3. [LEGADO_IMPORT_SAMPLE_MATRIX.md](./LEGADO_IMPORT_SAMPLE_MATRIX.md)

### 场景 B：我想知道导入失败为什么报这个错

按这个顺序看：

1. [LEGADO_IMPORT_ERROR_CODES.md](./LEGADO_IMPORT_ERROR_CODES.md)
2. [LEGADO_IMPORT_ISSUE_SCHEMA.md](./LEGADO_IMPORT_ISSUE_SCHEMA.md)
3. [LEGADO_IMPORT_TRACEABILITY_INDEX.md](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)

### 场景 C：我想补一个新的 alias / 样本 / 测试

按这个顺序看：

1. [LEGADO_FIELD_MAPPING_PHASE2.md](./LEGADO_FIELD_MAPPING_PHASE2.md)
2. [LEGADO_IMPORT_SAMPLE_MATRIX.md](./LEGADO_IMPORT_SAMPLE_MATRIX.md)
3. [LEGADO_IMPORT_TRACEABILITY_INDEX.md](./LEGADO_IMPORT_TRACEABILITY_INDEX.md)
4. [test_legado_import_api.py](../backend/tests/test_legado_import_api.py)

### 场景 D：我想接前端导入报错展示

按这个顺序看：

1. [LEGADO_IMPORT_ISSUE_SCHEMA.md](./LEGADO_IMPORT_ISSUE_SCHEMA.md)
2. [LEGADO_IMPORT_ERROR_CODES.md](./LEGADO_IMPORT_ERROR_CODES.md)
3. [LEGADO_IMPORT_SAMPLE_MATRIX.md](./LEGADO_IMPORT_SAMPLE_MATRIX.md)

## 6. 维护原则

对当前 Phase 2 静态 importer 的任何修改，都应遵守以下原则：

### 6.1 先看边界，再改代码

先确认：
- 是否仍属于静态 importer
- 是否会引入新的运行时概念
- 是否会突破当前白名单边界

### 6.2 改一个点，至少同步两处

如果你改了：

- 字段映射
  - 至少同步：
    - 字段映射文档
    - 样本矩阵 / 测试

- 错误码
  - 至少同步：
    - 错误码文档
    - issue schema
    - 测试

- 样本
  - 至少同步：
    - 样本矩阵
    - Traceability 索引
    - 测试注释 / 编号

### 6.3 不允许“偷偷扩运行时”

任何涉及以下内容的需求，都不能直接塞进当前 importer：

- JS
- Cookie / 登录态
- WebView
- 多请求链
- 复杂变量
- replace / 净化 DSL

这些必须单独评估阶段升级。

## 7. 当前状态结论

当前可以把 Phase 2 的状态理解为：

- **静态 importer 第一阶段核心实现已完成**
- **静态 importer 第一阶段验收闭环已完成**
- 已达到：
  - 可维护
  - 可追溯
  - 可解释
  - 可测试
- 当前可以：
  - 正式以文档化证据宣布当前 Phase 2 完成
  - 回到主线功能
  - 或未来再规划更高阶段

## 8. 后续方向建议

如果未来还继续推进，但仍不碰高兼容运行时，建议优先顺序如下：

1. 文档维护与清理
2. importer 测试可读性整理
3. 小范围静态 alias 增量支持
4. 更高阶段规划评估

如果未来确实要进入更高兼容阶段，建议单独新建阶段文档，不要直接在当前 Phase 2 文档上模糊扩展。

## 9. 相关代码入口

后端 importer 相关代码入口可从这些位置开始看：

- [legado_validator.py](../backend/app/services/online/legado_validator.py)
- [legado_mapper.py](../backend/app/services/online/legado_mapper.py)
- [legado_importer.py](../backend/app/services/online/legado_importer.py)
- [legado_import.py](../backend/app/schemas/legado_import.py)
- [online_source_import.py](../backend/app/routers/online_source_import.py)
- [test_legado_import_api.py](../backend/tests/test_legado_import_api.py)

## 10. 本文档维护约定

当以下内容发生变化时，应同步更新本文档：

- 新增或删除核心文档
- Phase 2 边界变化
- 文档导航关系变化
- importer 维护流程变化
- 阶段性结论变化

如果只是补单个 alias、样本或错误码，通常不需要改本文档；
但如果影响“阅读顺序 / 文档职责 / 边界理解”，就应同步更新。
