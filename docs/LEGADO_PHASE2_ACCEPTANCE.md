# Legado Phase 2 Acceptance（2026-03-17）

本文档用于固定当前仓库对 Legado Phase 2 的最终验收结论。

## 1. 验收范围

本次验收仅覆盖：

- Phase 2 静态 importer
- 严格白名单导入
- 静态字段映射
- 静态 alias / parser 归一化
- 稳定错误码
- 样例矩阵与 Traceability
- importer 与现有 discovery 执行链兼容

本次验收不覆盖：

- JS 执行
- Cookie / 登录态运行时
- WebView
- proxy 执行层
- 动态请求运行时
- 多请求链式运行时
- 高兼容 Legado 运行时

## 2. 验收结论

结论：

- `通过`

当前可以正式判定：

- `Phase 2 完成`

## 3. 验收依据

### 3.1 文档闭环

已具备以下文档：

- `LEGADO_PHASE2_INDEX.md`
- `LEGADO_FIELD_MAPPING_PHASE2.md`
- `LEGADO_IMPORT_ERROR_CODES.md`
- `LEGADO_IMPORT_SAMPLE_MATRIX.md`
- `LEGADO_IMPORT_TRACEABILITY_INDEX.md`
- `LEGADO_IMPORT_ISSUE_SCHEMA.md`
- `LEGADO_PHASE2_STATUS.md`
- `LEGADO_PHASE2_ACCEPTANCE.md`

### 3.2 错误码闭环

`backend/app/schemas/legado_import.py` 中定义的 21 个错误/警告码，当前均已具备：

- 实现
- 文档
- 样例矩阵
- Traceability
- 自动化测试

### 3.3 自动化验证

已执行：

```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_legado_import_api.py backend/tests/test_online_sources_api.py backend/tests/test_online_discovery_api.py -q
```

结果：

- `50 passed in 19.45s`

### 3.4 importer -> discovery 回归

已存在正式回归测试，覆盖：

- 导入 Legado 样例
- 导入成功并落库
- `detail` 成功
- `catalog` 成功
- `chapter` 成功

### 3.5 验收环境摘要

- 验收日期：`2026-03-17`
- 执行命令与测试结果：见 `3.3 自动化验证`
- 当前仓库本地可确认的工具版本：`Python 3.13.3`、`pytest 8.4.2`
- 当前文档未单独固化验收当日更多环境差异信息；后续复验应以仓库内容、执行命令与测试结果为准。

## 4. 本轮收尾完成项

- 补齐 9 个错误码的样例矩阵
- 补齐 9 个错误码的 Traceability
- 补齐 9 个错误码的 importer 自动化测试
- 补齐 import 后 `detail -> catalog -> chapter` 正式回归
- 修正 duplicate issue 行为
- 统一 Phase 2 状态文档口径

## 5. 验收后维护约定

如果后续继续维护当前 Phase 2：

- 新增字段支持前，必须先确认不突破静态 importer 边界
- 新增错误码时，必须同步更新样例矩阵、Traceability、测试
- 不允许把 JS / Cookie / WebView / 高兼容运行时偷偷并入当前 Phase 2

如果后续要进入更高兼容阶段：

- 必须新建后续阶段文档
- 不应直接模糊扩写当前 Phase 2 文档
