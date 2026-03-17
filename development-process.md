# AI Task Template

When implementing a new feature:

1. Read AGENTS.md
2. Read development-process.md
3. Scan project structure
4. Locate related files
5. Produce modification plan
6. Implement changes
7. Validate compatibility



# TXT Reader 开发实施流程

> 本文档用于指导 AI / 开发代理按阶段完成 TXT Reader 项目开发。  
> 目标是确保任务边界清晰、输出稳定、代码可运行，并便于后续迭代维护。

---

# 0. 全局约束

>***在执行任何开发任务前，必须先理解以下全局上下文与约束。***


你现在是我的全栈开发代理，请帮我开发一个“个人使用”的 TXT 在线阅读 Web 应用。

## 项目目标

开发一个“个人使用”的 TXT 在线阅读 Web 应用，具备以下能力：

- 上传 TXT 文件
- 自动解析章节
- 提供书架、书籍详情、目录、阅读页
- 支持手机和 PC 浏览器
- 阅读进度可跨设备同步
- 支持用户自定义“目录识别正则表达式”
- 前后端分离，但不过度工程化
- 代码必须真实可运行，不允许伪代码，不允许省略关键文件

## 技术栈

### 前端

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

### 后端

- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Python 3.11+

## 总体要求

1. 这是个人项目，但代码结构必须清晰。
2. 先做 MVP，后续可扩展。
3. 后端提供 REST API。
4. 文件保存在本地磁盘。
5. 数据库存储为 SQLite。
6. 不使用微服务、Redis、消息队列、K8s 等复杂基础设施。
7. 严格按每一轮任务输出代码。
8. 每一轮输出代码时必须使用以下格式：
9. 不允许输出“此处省略”。
10. 如果本轮只要求输出部分文件，就不要提前输出别的模块。
11. 优先保证能运行，再考虑花哨设计。

---

# 第一阶段：后端基础建设

---

## 第 1 轮：项目目录树与后端基础骨架

### 任务目标

先生成项目目录树和 `backend` 基础骨架，不生成 `frontend`。

### 需要输出

1. 项目目录树
2. backend 基础代码文件

### backend 目标

- FastAPI 项目基础可运行
- SQLite 可连接
- SQLAlchemy 基础配置完成
- CORS 配置完成
- API 路由总入口完成
- 统一配置文件完成
- 数据库初始化逻辑完成
- 上传目录和数据目录自动创建
- 提供基础 README 片段，说明后端如何启动

### 建议目录

至少包含以下内容：

- `app/main.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/security.py`
- `app/models/`
- `app/schemas/`
- `app/routers/`
- `app/services/`
- `app/utils/`
- `app/init_data.py`

### 要求

1. `main.py` 可直接启动
2. 提供 `/health` 接口
3. 提供基础 settings 配置
4. 提供 Base 和 Session 配置
5. 代码完整可运行
6. 暂时不实现书籍上传、章节解析、规则管理、阅读进度业务
7. 只输出本轮需要的 backend 文件

---

## 第 2 轮：数据库模型与基础 Schema

### 任务目标

在后端基础骨架上继续生成数据库模型、基础 Schema 和建表初始化逻辑。

### 只输出

- 新增或需要修改的 backend 文件
- 不输出 frontend

### 需要实现的表

#### 1. `users`

- id
- username
- password_hash
- created_at

#### 2. `books`

- id
- user_id
- title
- author
- description
- file_name
- file_path
- encoding
- total_words
- total_chapters
- chapter_rule_id
- created_at
- updated_at

#### 3. `book_chapters`

- id
- book_id
- chapter_index
- chapter_title
- start_offset
- end_offset
- created_at

#### 4. `reading_progress`

- id
- user_id
- book_id
- chapter_index
- char_offset
- percent
- updated_at

#### 5. `chapter_rules`

- id
- user_id
- rule_name
- regex_pattern
- flags
- description
- is_builtin
- is_default
- created_at
- updated_at

### 要求

1. SQLAlchemy 模型完整
2. 关系定义合理
3. 基础 Schema 一并生成，至少包含读写用的 Pydantic 模型
4. 增加数据库初始化逻辑，应用启动时可创建表
5. 暂时不写完整业务接口
6. 命名统一、代码可运行
7. 只输出新增或修改文件

---

## 第 3 轮：登录与认证

### 任务目标

实现最简认证系统，只做 backend。

### 目标

- 单用户优先
- 没有注册页
- 初始化一个默认用户
- 支持登录
- 支持获取当前用户信息

### 需要实现的接口

- `POST /api/auth/login`
- `GET /api/auth/me`

### 要求

1. 使用 JWT 或简洁 token 认证方案
2. 提供密码 hash 与校验逻辑
3. 应用首次运行时自动插入默认用户，例如：
- username: `admin`
- password: `admin123`
4. 提供认证依赖，供后续保护接口
5. `/api/auth/me` 返回当前登录用户基础信息
6. 错误处理清晰
7. 只输出新增或修改的 backend 文件

### 注意

- 这是个人项目，但仍然保留 `user` 表和鉴权流程
- 不生成注册接口

---

## 第 4 轮：目录规则系统初始化与基础管理

### 任务目标

实现 `chapter_rules` 的初始化和基础管理能力，只做 backend。

### 目标

- 应用启动时自动插入内置目录规则
- 能查询规则列表
- 能新增 / 编辑 / 删除自定义规则
- 内置规则不可删除

### 接口

- `GET /api/chapter-rules`
- `POST /api/chapter-rules`
- `PUT /api/chapter-rules/{rule_id}`
- `DELETE /api/chapter-rules/{rule_id}`

### 内置规则至少包括

1. 中文章节规则  
匹配“第1章 / 第十二章 / 第003章”

2. 英文章节规则  
匹配“Chapter 1 / CHAPTER 12”

3. 卷章混合规则  
匹配“第1卷 第2章”

4. 单章节全文模式  
特殊规则，不进行正则切分

### 规则字段

- id
- user_id
- rule_name
- regex_pattern
- flags
- description
- is_builtin
- is_default
- created_at
- updated_at

### 要求

1. `GET` 返回“内置规则 + 当前用户自定义规则”
2. 用户可以 CRUD 自定义规则
3. 内置规则不可删除，不可被普通编辑覆盖核心属性
4. 用户可以设置默认规则，但同一用户只能有一个默认规则
5. 只输出新增或修改的 backend 文件
6. 暂时不做“规则测试接口”和“书籍重新解析接口”

---

## 第 5 轮：正则编译、测试与预览

### 任务目标

实现目录规则测试能力，只做 backend。

### 需要实现

#### 工具函数

- `compile_regex(pattern, flags)`
- `test_rule_on_text(text, pattern, flags)`

#### 接口

- `POST /api/chapter-rules/test`

### 输入支持

- `book_id`
- 或原始文本片段 `text`
- `regex_pattern`
- `flags`

### 输出格式

```json
{
"matched": true,
"count": 1,
"items": [
 {
   "text": "第1章 开始",
   "start": 120,
   "end": 128
 }
]
}
```

### 要求

1. 支持 flags，如 `i`、`m`
2. 对非法正则、非法 flags 做异常捕获，返回友好错误
3. 如果传入 `book_id`，则从对应书籍文件中读取文本测试
4. 返回前 20 个匹配结果即可
5. 单章节全文模式单独处理，不真正执行正则
6. 只输出新增或修改的 backend 文件

---

## 第 6 轮：上传 TXT、编码检测与保存文件

### 任务目标

实现 TXT 书籍上传能力，只做 backend。

### 接口

- `POST /api/books/upload`

### 要求

1. 支持上传 TXT 文件
2. 将原始文件保存到本地磁盘
3. 自动检测编码，尽量支持：
- UTF-8
- GBK
- UTF-16
4. 将文本统一按 UTF-8 处理
5. 尝试自动识别书名，识别不到则使用文件名
6. 创建 `books` 记录
7. 上传时允许指定 `chapter_rule_id`
8. 暂时不要求完善书架列表接口，但上传成功后要返回书籍基础信息
9. 编码检测逻辑单独封装
10. 错误处理完整
11. 只输出新增或修改的 backend 文件

---

## 第 7 轮：章节切分逻辑

### 任务目标

实现章节切分逻辑，只做 backend。

### 需要实现的 service

- `split_book_into_chapters(text, rule)`

### 切分要求

1. 使用章节标题匹配结果进行切分
2. 每章存储：
- `chapter_index`
- `chapter_title`
- `start_offset`
- `end_offset`
3. `start_offset / end_offset` 基于原始文本字符位置
4. 如果未匹配到任何目录，则回退为单章节：
- `chapter_index = 0`
- `chapter_title = "全文"`
- `start_offset = 0`
- `end_offset = len(text)`
5. 单章节全文模式规则单独处理，不走正则
6. 切分逻辑要和数据库写入逻辑分开封装
7. 只输出新增或修改的 backend 文件

### 注意

- 这是项目核心能力，代码要尽量清晰
- 正则匹配到的标题文本可以直接作为章节标题

---

## 第 8 轮：上传后自动解析并保存章节

### 任务目标

在上传书籍后，自动完成章节切分并写入数据库，只做 backend。

### 需要实现

1. 上传成功后，根据 `chapter_rule_id` 或默认规则自动解析章节
2. 将解析结果写入 `book_chapters` 表
3. 更新 `books.total_chapters` 和 `books.total_words`
4. 如果未匹配到目录，自动保存为“全文”单章节
5. 保持上传接口返回完整书籍基础信息
6. 只输出新增或修改的 backend 文件

### 要求

- 如果解析失败，返回友好错误
- 如果只是“没有匹配到章节”，不能报错，必须降级为单章节模式

---

## 第 9 轮：书籍列表、详情、章节列表与章节正文

### 任务目标

实现书籍相关查询接口，只做 backend。

### 需要实现的接口

#### 书籍

- `GET /api/books`
- `GET /api/books/{book_id}`
- `DELETE /api/books/{book_id}`

#### 章节

- `GET /api/books/{book_id}/chapters`
- `GET /api/books/{book_id}/chapters/{chapter_index}`

### 要求

1. `GET /api/books` 返回当前用户书架列表
2. 支持按书名搜索
3. 返回字段包括：
- 书名
- 作者
- 总章节数
- 总字数
- 最近阅读时间（如果有）
- 阅读进度百分比（如果有）
4. `GET /api/books/{book_id}` 返回书籍详情和使用中的目录规则
5. `GET /api/books/{book_id}/chapters` 返回目录列表
6. `GET /api/books/{book_id}/chapters/{chapter_index}` 返回该章节正文内容
7. 正文接口必须按章节返回，不允许一次性返回整本书
8. `DELETE` 删除数据库记录和本地文件
9. 只输出新增或修改的 backend 文件

---

## 第 10 轮：重新解析目录

### 任务目标

实现“重新解析目录”能力，只做 backend。

### 接口

- `POST /api/books/{book_id}/reparse`

### 输入

- `chapter_rule_id`

### 行为

1. 根据指定规则重新解析该书
2. 先删除原有 `book_chapters`
3. 重新写入新的章节记录
4. 更新 `books.chapter_rule_id` 和 `total_chapters`
5. 返回解析后的章节摘要信息

### 要求

1. 如果规则无效，返回友好错误
2. 如果没有匹配到目录，也必须降级为单章节模式
3. 只输出新增或修改的 backend 文件

---

## 第 11 轮：阅读进度同步

### 任务目标

实现阅读进度同步接口，只做 backend。

### 接口

- `GET /api/books/{book_id}/progress`
- `PUT /api/books/{book_id}/progress`

### 字段要求

- user_id
- book_id
- chapter_index
- char_offset
- percent
- updated_at

### 行为要求

1. `GET` 返回当前用户在该书上的最新阅读进度
2. `PUT` 创建或更新阅读进度
3. 多端冲突时，以 `updated_at` 最新记录为准
4. `percent` 用于展示，定位仍以：
- `chapter_index`
- `char_offset`
为主
5. 书架列表中的最近阅读时间和阅读百分比应能基于该表计算或读取
6. 只输出新增或修改的 backend 文件

---

## 第 12 轮：后端收尾

### 任务目标

对 backend 做收尾整理。

### 请补充或完善

1. 全局异常处理
2. 统一响应错误格式
3. 必要的工具函数整理
4. 初始化脚本 / 种子数据逻辑整理
5. `requirements.txt`
6. `.env.example`
7. README 中 backend 启动说明
8. 确保导入路径、依赖关系、启动流程可运行

### 输出要求

- 只输出新增或修改的 backend 文件
- 不生成 frontend

## 第一阶段后端开发完成后对AI输入验收指令
```
请对 backend 做一次完整自检：
- 能否启动
- 路由是否注册成功
- 数据库是否初始化成功
- 认证接口是否可用
- 书籍上传接口是否可用
- 章节解析接口是否可用
- 阅读进度接口是否可用
如果有问题，直接修复。
```
---

# 第二阶段：前端开发

---

## 第 13 轮：前端项目骨架

### 任务目标

开始生成 frontend，先只生成前端基础骨架，不修改 backend。

### 技术栈

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

### 请实现

1. frontend 项目目录树
2. 基础入口文件
3. 路由基础配置
4. Pinia 基础配置
5. 基础 layout
6. API 请求封装
7. token 存储逻辑
8. 路由鉴权守卫
9. 基础样式文件

### 页面先只留占位

- 登录页
- 书架页
- 书籍详情页
- 阅读页
- 规则管理页

### 要求

1. 前端可以启动
2. 已登录才能访问业务页
3. API 基础封装完整
4. 只输出 frontend 文件

---

## 第 14 轮：登录页与认证状态

### 任务目标

实现前端登录流程，只修改 frontend。

### 请实现

1. 登录页
2. auth store
3. 调用：
- `POST /api/auth/login`
- `GET /api/auth/me`
4. 登录成功后保存 token
5. 刷新页面后自动恢复登录态
6. 未登录访问业务页时跳回登录页
7. 提供基础错误提示和加载态

### 要求

- UI 简洁整洁
- 使用 Naive UI
- 只输出新增或修改的 frontend 文件

---

## 第 15 轮：书架页

### 任务目标

实现前端书架页，只修改 frontend。

### 请实现

1. 书架页展示书籍列表
2. 调用 `GET /api/books`
3. 支持按书名搜索
4. 支持上传 TXT
5. 支持删除书籍
6. 支持点击进入书籍详情
7. 支持点击继续阅读

### 展示字段

- 书名
- 作者
- 总章节数
- 总字数
- 最近阅读时间
- 阅读进度百分比
- 默认封面占位

### 要求

1. 使用 Naive UI
2. 页面在手机和桌面端都可用
3. 上传后刷新列表
4. 只输出新增或修改的 frontend 文件

---

## 第 16 轮：书籍详情页

### 任务目标

实现前端书籍详情页，只修改 frontend。

### 请实现

1. 调用 `GET /api/books/{book_id}`
2. 调用 `GET /api/books/{book_id}/chapters`
3. 展示：
- 书名
- 作者
- 文件信息
- 总章节数
- 总字数
- 当前使用的目录规则
- 目录列表
4. 提供：
- 开始阅读 / 继续阅读按钮
- 重新解析目录入口
5. 页面适配手机和桌面端

### 要求

- UI 简洁
- 目录列表可点击跳转阅读页
- 只输出新增或修改的 frontend 文件

---

## 第 17 轮：规则管理页

### 任务目标

实现前端目录规则管理页，只修改 frontend。

### 页面能力

1. 获取规则列表：
- `GET /api/chapter-rules`
2. 展示内置规则和自定义规则
3. 新增自定义规则
4. 编辑自定义规则
5. 删除自定义规则
6. 设置默认规则
7. 支持输入：
- `rule_name`
- `regex_pattern`
- `flags`
- `description`

### 要求

1. 内置规则不可删除
2. 使用表格 + 弹窗表单实现
3. UI 使用 Naive UI
4. 只输出新增或修改的 frontend 文件

---

## 第 18 轮：规则测试与预览

### 任务目标

在规则管理页中加入“测试规则”能力，只修改 frontend。

### 请实现

1. 调用 `POST /api/chapter-rules/test`
2. 支持两种测试方式：
- 选择一本已上传的书测试
- 输入原始文本片段测试
3. 展示返回结果：
- matched
- count
- items
4. 匹配结果列表显示：
- 匹配文本
- start
- end
5. 为 `regex_pattern` 输入框提供示例提示
6. 对错误正则显示友好报错

### 要求

- 测试区可放在规则管理页中
- 只输出新增或修改的 frontend 文件

---

## 第 19 轮：重新解析目录前端流程

### 任务目标

在前端实现“将规则用于某本书并重新解析”的交互，只修改 frontend。

### 请实现

1. 在书籍详情页提供“重新解析目录”操作
2. 可选择目录规则
3. 调用 `POST /api/books/{book_id}/reparse`
4. 重新解析成功后刷新：
- 书籍详情
- 目录列表
5. 在规则管理页中也可选择一本书并快速应用某条规则进行重解析

### 要求

- 交互清晰
- 有加载态和成功 / 失败提示
- 只输出新增或修改的 frontend 文件

---

## 第 20 轮：阅读页

### 任务目标

实现前端阅读页，只修改 frontend。

### 请实现

1. 调用：
- `GET /api/books/{book_id}/chapters`
- `GET /api/books/{book_id}/chapters/{chapter_index}`
- `GET /api/books/{book_id}/progress`
2. 页面打开时获取最新阅读进度并定位到对应章节
3. 阅读页支持：
- 正文显示
- 上一章 / 下一章
- 当前章节标题
- 当前进度展示
- 字体大小调节
- 行高调节
- 浅色 / 深色主题
4. 设置项保存到 `localStorage`
5. 桌面端显示侧边目录
6. 手机端目录使用 Drawer

### 要求

1. UI 整洁，适合阅读
2. 正文区域排版舒适
3. 只输出新增或修改的 frontend 文件

---

## 第 21 轮：阅读进度自动同步

### 任务目标

在前端阅读页实现阅读进度自动同步，只修改 frontend。

### 请实现

1. 调用 `PUT /api/books/{book_id}/progress`
2. 同步字段：
- `chapter_index`
- `char_offset`
- `percent`
3. 同步策略：
- 切换章节时立即保存
- 阅读过程中节流保存，例如 15 秒一次
- 页面关闭前尝试保存一次
4. 页面加载时优先使用服务端进度
5. `percent` 用于展示
6. 实际定位优先基于：
- `chapter_index`
- `char_offset`

### 要求

1. 不要只靠总百分比定位
2. 尽量避免频繁请求
3. 只输出新增或修改的 frontend 文件

---

## 第 22 轮：前端收尾

### 任务目标

对 frontend 做收尾整理，只修改 frontend。

### 请补充或完善

1. 全局错误提示
2. 页面加载态
3. 空状态
4. API 类型定义整理
5. 组件抽离（如需要）
6. 响应式布局细节优化
7. 代码中明显重复逻辑的整理
8. README 中 frontend 启动说明

### 要求

- 不大改已有接口对接方式
- 以可运行、可联调为优先
- 只输出新增或修改的 frontend 文件

## 第二阶段前端开发完成后对AI输入验收指令

```
请对 frontend 做一次完整自检：
- 能否安装依赖并启动
- 路由是否正常
- 登录流程是否正常
- API 请求是否能正确对接 backend
- 页面是否存在明显类型错误或导入错误
如果有问题，直接修复。
```
## 联调时对AI输入验收指令
```
请站在联调角度检查整个项目：
- 前后端接口路径是否一致
- 请求字段和返回结构是否一致
- token 是否正确传递
- 阅读页是否能恢复进度
- 重新解析目录后目录列表是否刷新
如果发现问题，直接修复代码。
```
---

# 第三阶段：工程化交付与联调

---

## 第 23 轮：README、Docker 与启动方式

### 任务目标

生成项目交付文件。

### 请输出

1. 根目录 `README.md`
2. `backend/requirements.txt`（如还未完善）
3. `frontend/package.json`（如需补充）
4. `backend/Dockerfile`
5. `frontend/Dockerfile`
6. `docker-compose.yml`
7. `.gitignore`
8. `.env.example`

### README 必须包含

- 项目简介
- 技术栈
- 目录结构
- 本地开发启动方式
- Docker 启动方式
- 默认账号密码
- 目录规则功能说明
- 重新解析目录说明
- 阅读进度同步说明

### 要求

- 内容完整
- 命令可执行
- 不要只给模板占位

---

## 第 24 轮：联调与修复

### 任务目标

站在“联调与验收”的角度检查整个项目，列出并修复潜在问题。

### 重点检查

1. 前后端接口路径是否一致
2. 请求字段名是否一致
3. 返回结构是否一致
4. token 传递是否一致
5. `chapter_rule_id` 的使用是否一致
6. 阅读进度字段是否一致
7. 阅读页加载逻辑是否能正确恢复进度
8. 重新解析目录后页面是否正确刷新
9. 移动端目录抽屉是否正常工作
10. Docker 与本地启动命令是否一致可用

### 输出要求

1. 先列出发现的问题
2. 再输出对应修复文件
3. 只输出新增或修改的文件
4. 不要空谈，要直接改代码

### 实际使用时的建议

1. 先发第 0 段
2. 再发第 1～12 段，把后端做完
3. 跑一次后端，看报错
4. 再发第 13～22 段做前端
5. 最后发第 23、24 段做交付和修复

### 两个很有用的补刀提示

当 AI 开始偷懒时，你可以追加这两段。

**补刀 1：禁止省略**

```
不要省略文件，不要只给思路，不要输出伪代码。
请直接输出完整可运行代码。
如果需要修改旧文件，请给出修改后的完整文件内容。
```

**补刀 2：强制修复**

```
不要解释为什么复杂，请直接修复。
如果你发现前面生成的代码有问题，请以当前轮次为准直接改掉。
优先保证项目能运行和联调通过。
```
---
### 实际使用时的建议
---
1. 先发第 0 段
2. 再发第 1～12 段，把后端做完
3. 跑一次后端验收指令，看报错
4. 再发第 13～22 段做前端
5. 跑一次前端验收指令，看报错
6. 最后发第 23、24 段做交付和修复
7. Ai修改完毕后即可通过Docker部署使用


---

# 第四阶段：在线阅读与阅读3（Legado）兼容扩展

> 本阶段用于在现有 TXT 阅读项目基础上，新增在线阅读能力，并通过多阶段演进，逐步接近阅读3原书源规则兼容。
> 该阶段必须在前三阶段稳定后再启动，不允许跳过项目扫描直接大规模实现。

## 适用前提

当需求涉及以下任一项时，进入本阶段：

- 在线阅读
- 网络书源
- 阅读3（Legado）书源导入
- 阅读3规则兼容
- 登录态 / Cookie / 反爬 / WebView 类抓取能力

---

## Phase 0：项目扫描与架构评估

### 任务目标
- 扫描现有前后端结构
- 明确本地 TXT 阅读链路与在线阅读接入点
- 识别哪些模块可以复用，哪些模块必须新增
- 明确在线书籍与本地书籍如何共存

### 必须检查
#### Frontend
- 书架页
- 图书详情页
- 阅读页
- `api`
- `stores`
- `router`

#### Backend
- `routers`
- `services`
- `models`
- 本地 TXT 导入与解析链路
- 阅读进度与阅读设置相关模块

### 本阶段必须输出
- 项目扫描结果
- 可复用模块
- 必改模块
- 建议新增模块
- 风险点
- 分阶段路线

### 本阶段禁止
- 未扫描项目就直接实现在线书源引擎
- 将在线书源逻辑直接并入 TXT 本地解析逻辑
- 直接以“高兼容阅读3原书源”为首轮实现目标

---

## Phase 1：最小在线阅读能力

### 任务目标
实现最小可运行的在线阅读链路，使在线书籍可进入现有阅读流程。

### 建议支持能力
- 公开网页书源
- 搜索 / 详情 / 目录 / 正文
- GET / POST
- 基础 Header
- CSS / JSoup
- JSONPath
- XPath
- 正则
- 基础内容清洗与正文提取

### 建议新增模块
- `source_engine`
- `rule_parser`
- `source_importer`
- `source_validator`
- `online_book_service`
- `fetch_service`
- `content_parse_service`

### 验收重点
- 不破坏现有 TXT 本地阅读
- 在线书籍可以完成搜索、详情、目录、正文完整链路
- 在线书籍可进入现有书架 / 阅读页
- 架构具备后续扩展空间

### 本阶段暂不做
- JS 执行
- 登录态
- Cookie
- 复杂反爬
- WebView 类规则

---

## Phase 2：阅读3常见规则子集兼容

### 任务目标
支持导入阅读3书源 JSON，并兼容常见规则组合。

### 建议支持能力
- 阅读3书源 JSON 导入
- 字段映射与规则标准化
- CSS / JSoup
- JSONPath
- XPath
- 正则
- 常见替换规则
- 常见目录规则
- 基础变量能力
- 书源测试 / 调试能力

### 验收重点
- 常见阅读3书源可以导入
- 导入后可完成搜索 / 详情 / 目录 / 正文链路
- 调试工具足以定位常见规则失败原因
- 不显著破坏项目可维护性

---

## Phase 3：高级兼容能力

### 任务目标
逐步支持阅读3高复杂度能力。

### 建议纳入能力
- 登录态
- Cookie
- 会话维持
- 更复杂 Header / 请求参数
- 反爬处理
- JS 执行
- WebView 类规则或替代实现策略

### 建议新增模块
- `session_handler`
- `cookie_store`
- `js_execution_sandbox`
- `anti_bot_handler`
- `webview_strategy`（或等价替代模块）

### 验收重点
- 高风险能力模块化隔离
- 有超时、失败回退、错误提示、资源控制
- 不影响基础在线阅读链路稳定性

---

## Phase 4：高兼容收尾与兼容率提升

### 任务目标
提升阅读3原书源导入后的整体可用率和兼容率。

### 重点内容
- 高频失败书源回归
- 高频失败场景补齐
- 规则执行边界修复
- 调试能力与错误提示增强
- 兼容率提升验证

### 验收重点
- 常见书源兼容率提升有明确结果
- 高频失败场景有明确归因和修复路径
- 不以牺牲系统可维护性换取短期兼容率

---

## 第四阶段实施规则

当执行在线阅读 / 阅读3兼容任务时，必须遵守：

1. 先评估，后实施
2. 先最小可运行，后扩展兼容
3. 先高频可控能力，后高风险能力
4. 每个阶段独立验收，避免一次性失控
5. 始终保证现有本地 TXT 阅读能力不被破坏