# Legado Phase 2 状态（2026-03-17）

本文档用于回答两个问题：

1. Phase 2 文档整理是否完成
2. Phase 2 整体功能与验收是否完成

当前结论：

- 文档整理：`已完成`
- Phase 2 核心实现：`已完成`
- Phase 2 验收闭环：`已完成`
- 当前可以正式判定：`Phase 2 完成`

## 1. 状态摘要

| 维度 | 当前状态 | 说明 |
|---|---|---|
| 文档总览/字段映射/错误码/样例矩阵/Traceability/Issue Schema | 已完成 | 相关文档已齐备并互相引用 |
| importer 接口与落库 | 已完成 | `/api/online-sources/import/validate` 与 `/api/online-sources/import` 可执行 |
| 字段映射与冻结口径 | 已完成 | `selector@text`、`selector@html`、`warning + ignore`、bridge placeholder 已有实现与测试 |
| 错误码全集闭环 | 已完成 | 21 个错误/警告码已完成“实现 -> 样例矩阵 -> Traceability -> 自动化测试”闭环 |
| Traceability 到实现与测试 | 已完成 | Traceability 已补实现入口与新增样例/测试映射 |
| import 后 discovery 正式回归 | 已完成 | 已补 importer -> `detail -> catalog -> chapter` 正式回归测试 |
| duplicate issue 行为 | 已修正 | Authorization / Multi Request 不再重复输出同码同路径 issue |

## 2. 本轮收尾完成内容

### 2.1 补齐 9 个错误码闭环

本轮补齐了以下错误码的文档与测试闭环：

- `LEGADO_UNSUPPORTED_AUTHORIZATION`
- `LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE`
- `LEGADO_UNSUPPORTED_CONDITION_DSL`
- `LEGADO_UNSUPPORTED_METHOD`
- `LEGADO_UNSUPPORTED_MULTI_REQUEST`
- `LEGADO_UNSUPPORTED_DYNAMIC_REQUEST`
- `LEGADO_INVALID_URL`
- `LEGADO_REQUIRED_FIELD_MISSING`
- `LEGADO_MAPPING_FAILED`

对应新增样例：

- `S21` -> Authorization header
- `S22` -> dynamic variable
- `S23` -> condition DSL
- `S24` -> unsupported method
- `S25` -> multi request
- `S26` -> dynamic request
- `S27` -> invalid base URL
- `S28` -> missing required top-level stage field
- `S29` -> invalid stage shape

### 2.2 importer 正式回归补齐

已在 `backend/tests/test_legado_import_api.py` 中补齐：

- 9 条错误码回归测试
- 1 条 importer -> discovery 正式回归：
  - 导入成功并落库
  - `detail` 成功
  - `catalog` 成功
  - `chapter` 成功

### 2.3 duplicate issue 最小修正

本轮没有保留 duplicate issue 行为，而是做了最小修正：

- 对已判定为 forbidden 的顶层字段不再继续递归追加无关错误
- `header` 走专门校验路径，避免与通用递归校验重复报错
- 顶层阶段字段 `ruleSearch / ruleBookInfo / ruleToc / ruleContent` 的 `stage` 元信息已对齐到语义阶段

结果：

- `LEGADO_UNSUPPORTED_AUTHORIZATION` 不再重复报错
- `LEGADO_UNSUPPORTED_MULTI_REQUEST` 不再重复报错
- `LEGADO_UNSUPPORTED_DYNAMIC_VARIABLE` 不再被额外污染出 `LEGADO_UNSUPPORTED_LOGIN_STATE`

## 3. 验证证据

2026-03-17 已执行：

```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_legado_import_api.py backend/tests/test_online_sources_api.py backend/tests/test_online_discovery_api.py -q
```

结果：

- `50 passed in 19.45s`

这组验证覆盖了：

- importer validate / import
- Phase 2 错误码回归
- online source validation
- discovery search/detail/catalog/chapter
- importer 与现有 discovery 执行链兼容

## 4. 边界检查

本轮收尾未扩展 Phase 2 边界。

仍然未纳入当前 Phase 2 的能力：

- JS 执行
- Cookie / 登录态运行时
- WebView
- proxy 执行层
- 多请求链式运行时
- 复杂变量系统运行时
- 条件 DSL 运行时
- replace / clean DSL 运行时
- 高兼容运行时

本轮工作仅完成：

- 文档闭环
- 样例闭环
- Traceability 闭环
- 自动化测试闭环
- duplicate issue 最小修正

## 5. 最终判断

当前可以正式使用以下口径：

> Phase 2 的静态 importer 第一阶段已经完成核心实现，并已完成验收闭环；当前可以正式判定 “Phase 2 完成”。

如后续继续推进：

- 小范围静态 alias / 静态字段增量支持，仍应视为当前 Phase 2 的维护工作
- 任何 JS / Cookie / WebView / 高兼容运行时相关需求，必须进入后续新阶段讨论
