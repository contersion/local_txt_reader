# Project Guidance

本项目是个人使用的 TXT 在线阅读器，支持书架、目录、阅读进度同步和用户自定义章节正则。

## Stack
- Frontend: Vue 3 + Vite + TypeScript + Vue Router + Pinia + Naive UI
- Backend: FastAPI + SQLAlchemy + SQLite

## Architecture Rules
- 使用轻量前后端分离
- 不要引入微服务、Redis、MQ、K8s
- 阅读正文必须按章节返回，不能整本返回
- 阅读进度以 chapter_index + char_offset 为主，percent 仅用于展示
- 章节解析支持内置规则和用户自定义 regex
- 没匹配到章节时必须降级为“全文”单章节模式

## Workflow
详细开发步骤见 `docs/IMPLEMENTATION_STEPS.md`。
进行较大功能开发、重构、验收前，先阅读该文件。

## Commands
- backend: `uvicorn app.main:app --reload`
- frontend: `npm run dev`
- docker: see README

## Reading Page Refactor Rules
- 阅读页允许进行 UI 重构与前端交互重构，但不得修改后端接口、数据库结构、API 字段语义。
- 阅读正文仍必须按章节加载与返回，不能改为整本返回。
- 阅读进度定位仍以 `chapter_index + char_offset` 为主，`percent` 仅用于展示。
- 目录、阅读设置、主题、字体大小、行高、进度同步等现有能力应尽量复用，不要重写业务层。
- 阅读页需同时兼容 PC 与移动端，优先通过响应式布局、抽屉、浮动工具区实现。
- 允许将目录与设置从常驻面板改为抽屉式交互，但必须保持原有功能可用。

## Online Reading & Legado Compatibility Rules
当需求涉及“在线阅读”“网络书源”“阅读3（Legado）书源兼容”时，必须遵守以下原则：

### 1. 架构原则
- 在线阅读能力必须与现有本地 TXT 阅读能力解耦设计。
- 不允许将在线书源解析逻辑直接硬塞进现有 TXT 本地解析链路。
- 后端应新增独立的 `source engine / parser engine` 类模块，用于承载书源规则解析、请求执行、内容提取、正文解析等能力。
- 前端应将“本地书籍”和“在线书籍”视为可共存的两类来源，但尽量复用现有书架、阅读页、阅读偏好、阅读进度能力。

### 2. 迭代原则
- 阅读3兼容必须分阶段推进，不允许一开始就以“接近完美兼容”作为首轮实现目标直接开工。
- 第一阶段只允许实现最小可运行的在线阅读能力与规则子集。
- JavaScript 执行、Cookie / 登录态、反爬、WebView 类规则等高风险能力必须后置。
- 每个阶段都必须有清晰边界、可独立验证、可独立回退。

### 3. 兼容原则
- 兼容阅读3书源规则时，应优先支持高频、可控、可验证的规则能力：
  - HTTP 请求
  - GET / POST
  - CSS / JSoup
  - JSONPath
  - XPath
  - 正则
- 高复杂度能力如 JS 执行、变量系统增强、登录态、Cookie、反爬、WebView 类规则，应视为高级兼容能力，单独评估后再纳入。
- 兼容目标应明确区分：
  - 在线阅读基础版
  - 阅读3常见规则子集兼容
  - 接近完美兼容阅读3原书源

### 4. 安全与风险原则
- 涉及外部网页抓取、JS 执行、登录态、Cookie、反爬的能力，必须单独评估安全风险。
- 涉及脚本执行时，必须考虑隔离、沙箱、超时、资源限制与错误恢复。
- 不允许为了兼容性而破坏现有本地 TXT 阅读稳定性。
- 不允许在未完成架构评估前直接进入大规模实现。

### 5. 开发流程原则
- 任何在线阅读 / 阅读3兼容需求，必须先：
  1. 阅读 `AGENTS.md`
  2. 阅读 `development-process.md`
  3. 扫描项目结构
  4. 输出可行性评估与阶段性方案
  5. 经确认后再进入具体实现
- 输出方案时必须明确：
  - 可复用模块
  - 必改模块
  - 建议新增模块
  - 风险点
  - 暂缓项