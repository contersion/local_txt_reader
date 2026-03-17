第 0 段：总约束
先发这一段，让 AI 先建立整体上下文。

你现在是我的全栈开发代理，请帮我开发一个“个人使用”的 TXT 在线阅读 Web 应用。

项目目标：
- 上传 txt 文件
- 自动解析章节
- 有书架、书籍详情、目录、阅读页
- 支持手机和 PC 浏览器
- 阅读进度可跨设备同步
- 支持用户自定义“目录识别正则表达式”
- 前后端分离，但不要过度工程化
- 代码必须真实可运行，不要伪代码，不要省略关键文件

技术栈固定如下：

前端：
- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

后端：
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Python 3.11+

总体要求：
1. 这是个人项目，但代码结构要清晰。
2. 先做 MVP，但后续可扩展。
3. 后端提供 REST API。
4. 文件保存在本地磁盘。
5. 数据库存储为 SQLite。
6. 不要使用微服务、Redis、消息队列、K8s 等复杂基础设施。
7. 请严格按我每一轮的任务输出代码。
8. 每一轮输出时请使用：
   ```filepath
   // 完整文件内容
不要输出“此处省略”。

如果本轮只要求输出部分文件，就不要提前输出别的模块。

优先保证能运行，再考虑花哨设计。


---

# 第 1 段：先生成项目目录树和后端基础骨架
这一段先让 AI 把后端架子搭起来，不要马上做前端。

```text
第一轮任务：先只生成项目目录树和 backend 基础骨架，不要生成 frontend。

请输出：

1. 项目目录树
2. backend 的基础代码文件

backend 目标：
- FastAPI 项目基础可运行
- SQLite 可连接
- SQLAlchemy 基础配置完成
- CORS 配置完成
- API 路由总入口完成
- 统一配置文件完成
- 数据库初始化逻辑完成
- 上传目录和数据目录自动创建
- 提供基础 README 片段说明后端如何启动

本轮不要实现具体业务，只搭骨架。

backend 目录建议至少包含：
- app/main.py
- app/core/config.py
- app/core/database.py
- app/core/security.py
- app/models/
- app/schemas/
- app/routers/
- app/services/
- app/utils/
- app/init_data.py

要求：
1. main.py 可直接启动。
2. 提供 /health 接口。
3. 提供基础 settings 配置。
4. 提供 Base 和 Session 配置。
5. 代码要完整可运行。
6. 暂时不要写书籍上传、章节解析、规则管理、阅读进度业务。
7. 只输出本轮需要的 backend 文件。
第 2 段：生成数据库模型
这一段只做模型和表结构。

第二轮任务：在上一轮 backend 基础上，继续生成数据库模型、基础 schema 和建表初始化逻辑。

请只输出新增或需要修改的 backend 文件，不要输出 frontend。

请实现以下表模型：

1. users
- id
- username
- password_hash
- created_at

2. books
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

3. book_chapters
- id
- book_id
- chapter_index
- chapter_title
- start_offset
- end_offset
- created_at

4. reading_progress
- id
- user_id
- book_id
- chapter_index
- char_offset
- percent
- updated_at

5. chapter_rules
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

要求：
1. SQLAlchemy 模型完整。
2. 关系定义合理。
3. 基础 schema 也一并生成，至少包含读写用的 Pydantic 模型。
4. 增加数据库初始化逻辑，应用启动时可创建表。
5. 暂时不要写完整业务接口。
6. 请保持命名统一、可运行。
7. 只输出新增或修改文件。
第 3 段：登录和认证
先把登录体系定下来。

第三轮任务：实现最简认证系统，只做 backend。

目标：
- 单用户优先
- 没有注册页
- 初始化一个默认用户
- 支持登录
- 支持获取当前用户信息

请实现：

接口：
- POST /api/auth/login
- GET /api/auth/me

要求：
1. 使用 JWT 或简洁 token 认证方案。
2. 提供密码 hash 与校验逻辑。
3. 应用首次运行时自动插入默认用户，例如：
   - username: admin
   - password: admin123
4. 需要有认证依赖，可用于后续保护接口。
5. /api/auth/me 返回当前登录用户基础信息。
6. 错误处理要清晰。
7. 只输出新增或修改的 backend 文件。

注意：
- 这是个人项目，但仍要保留 user 表和鉴权流程。
- 不要生成注册接口。
第 4 段：目录规则系统的数据与内置规则初始化
先把“规则”这块打牢。

第四轮任务：实现 chapter_rules 的初始化和基础管理能力，只做 backend。

目标：
- 应用启动时自动插入内置目录规则
- 能查询规则列表
- 能新增/编辑/删除自定义规则
- 内置规则不可删除

请实现接口：
- GET /api/chapter-rules
- POST /api/chapter-rules
- PUT /api/chapter-rules/{rule_id}
- DELETE /api/chapter-rules/{rule_id}

内置规则至少包括：
1. 中文章节规则
   - 匹配“第1章 / 第十二章 / 第003章”
2. 英文章节规则
   - 匹配“Chapter 1 / CHAPTER 12”
3. 卷章混合规则
   - 匹配“第1卷 第2章”
4. 单章节全文模式
   - 特殊规则，不进行正则切分

规则字段：
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

要求：
1. GET 返回“内置规则 + 当前用户自定义规则”。
2. 用户可以 CRUD 自定义规则。
3. 内置规则不可删除，不可被普通编辑覆盖核心属性。
4. 用户可以设置默认规则，但同一用户只能有一个默认规则。
5. 只输出新增或修改的 backend 文件。
6. 暂时不要做“规则测试接口”和“书籍重新解析接口”。
第 5 段：正则编译、测试、预览能力
这是规则系统的关键点。

第五轮任务：实现目录规则测试能力，只做 backend。

请实现以下能力：

1. 封装正则工具函数：
- compile_regex(pattern, flags)
- test_rule_on_text(text, pattern, flags)

2. 提供接口：
- POST /api/chapter-rules/test

输入支持：
- book_id 或 原始文本片段 text
- regex_pattern
- flags

输出：
- matched: bool
- count: int
- items: [
    {
      "text": "第1章 开始",
      "start": 120,
      "end": 128
    }
  ]

要求：
1. 支持 flags，如 i、m。
2. 对非法正则、非法 flags 做异常捕获，返回友好错误。
3. 如果传入 book_id，则从对应书籍文件中读取文本测试。
4. 返回前 20 个匹配结果即可。
5. 单章节全文模式单独处理，不要真的执行正则。
6. 只输出新增或修改的 backend 文件。
第 6 段：上传 txt、编码检测、保存文件
这一段把上传链路做出来。

第六轮任务：实现 txt 书籍上传能力，只做 backend。

请实现：

接口：
- POST /api/books/upload

要求：
1. 支持上传 txt 文件。
2. 将原始文件保存到本地磁盘。
3. 自动检测编码，尽量支持：
   - UTF-8
   - GBK
   - UTF-16
4. 将文本统一按 UTF-8 处理。
5. 尝试自动识别书名，识别不到则使用文件名。
6. 创建 books 记录。
7. 上传时允许指定 chapter_rule_id。
8. 暂时先不要求完善书架列表接口，但上传成功后要返回书籍基础信息。
9. 编码检测逻辑单独封装。
10. 错误处理完整。
11. 只输出新增或修改的 backend 文件。
第 7 段：章节切分逻辑
现在开始做解析核心。

第七轮任务：实现章节切分逻辑，只做 backend。

请实现 service：
- split_book_into_chapters(text, rule)

切分要求：
1. 使用章节标题匹配结果进行切分。
2. 每章存储：
   - chapter_index
   - chapter_title
   - start_offset
   - end_offset
3. start_offset / end_offset 基于原始文本字符位置。
4. 如果未匹配到任何目录，则回退为单章节：
   - chapter_index = 0
   - chapter_title = "全文"
   - start_offset = 0
   - end_offset = len(text)
5. 单章节全文模式规则要单独处理，不走正则。
6. 切分逻辑要和数据库写入逻辑分开封装。
7. 只输出新增或修改的 backend 文件。

注意：
- 这是项目核心能力，代码要尽量清晰。
- 正则匹配到的标题文本可以直接作为章节标题。
第 8 段：上传后自动解析并保存章节
把上传和解析串起来。

第八轮任务：在上传书籍后，自动完成章节切分并写入数据库，只做 backend。

请实现：
1. 上传成功后，根据 chapter_rule_id 或默认规则自动解析章节。
2. 将解析结果写入 book_chapters 表。
3. 更新 books.total_chapters 和 books.total_words。
4. 如果未匹配到目录，自动保存为“全文”单章节。
5. 保持上传接口返回完整书籍基础信息。
6. 只输出新增或修改的 backend 文件。

要求：
- 如果解析失败，返回友好错误。
- 但如果只是“没有匹配到章节”，不能报错，必须降级为单章节模式。
第 9 段：书籍列表、详情、章节列表、章节正文
这一步让阅读基础 API 齐了。

第九轮任务：实现书籍相关查询接口，只做 backend。

请实现接口：

书籍：
- GET /api/books
- GET /api/books/{book_id}
- DELETE /api/books/{book_id}

章节：
- GET /api/books/{book_id}/chapters
- GET /api/books/{book_id}/chapters/{chapter_index}

要求：
1. GET /api/books 返回当前用户书架列表。
2. 支持按书名搜索。
3. 返回字段包括：
   - 书名
   - 作者
   - 总章节数
   - 总字数
   - 最近阅读时间（如果有）
   - 阅读进度百分比（如果有）
4. GET /api/books/{book_id} 返回书籍详情和使用中的目录规则。
5. GET /api/books/{book_id}/chapters 返回目录列表。
6. GET /api/books/{book_id}/chapters/{chapter_index} 返回该章节正文内容。
7. 正文接口必须按章节返回，不允许一次性返回整本书。
8. DELETE 删除数据库记录和本地文件。
9. 只输出新增或修改的 backend 文件。
第 10 段：重新解析目录
把自定义规则真正落到书籍上。

第十轮任务：实现“重新解析目录”能力，只做 backend。

请实现接口：
- POST /api/books/{book_id}/reparse

输入：
- chapter_rule_id

行为：
1. 根据指定规则重新解析该书。
2. 先删除原有 book_chapters。
3. 重新写入新的章节记录。
4. 更新 books.chapter_rule_id 和 total_chapters。
5. 返回解析后的章节摘要信息。

要求：
1. 如果规则无效，返回友好错误。
2. 如果没有匹配到目录，也必须降级为单章节模式。
3. 只输出新增或修改的 backend 文件。
第 11 段：阅读进度同步
这是多端同步核心。

第十一轮任务：实现阅读进度同步接口，只做 backend。

请实现接口：
- GET /api/books/{book_id}/progress
- PUT /api/books/{book_id}/progress

字段要求：
- user_id
- book_id
- chapter_index
- char_offset
- percent
- updated_at

行为要求：
1. GET 返回当前用户在该书上的最新阅读进度。
2. PUT 创建或更新阅读进度。
3. 多端冲突时，以 updated_at 最新记录为准。
4. percent 用于展示，定位仍以：
   - chapter_index
   - char_offset
   为主。
5. 书架列表中的最近阅读时间和阅读百分比应能基于该表计算或读取。
6. 只输出新增或修改的 backend 文件。
第 12 段：后端收尾
这一步主要让后端变得更像可交付项目。

第十二轮任务：对 backend 做收尾整理。

请补充或完善：
1. 全局异常处理
2. 统一响应错误格式
3. 必要的工具函数整理
4. 初始化脚本/种子数据逻辑整理
5. requirements.txt
6. .env.example
7. README 中 backend 启动说明
8. 确保导入路径、依赖关系、启动流程可运行

只输出新增或修改的 backend 文件。
不要生成 frontend。
接下来开始前端。

第 13 段：前端项目骨架
先把框架搭起来。

第十三轮任务：开始生成 frontend，先只生成前端基础骨架，不要修改 backend。

技术栈固定：
- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

请实现：
1. frontend 项目目录树
2. 基础入口文件
3. 路由基础配置
4. Pinia 基础配置
5. 基础 layout
6. API 请求封装
7. token 存储逻辑
8. 路由鉴权守卫
9. 基础样式文件

页面先只留占位：
- 登录页
- 书架页
- 书籍详情页
- 阅读页
- 规则管理页

要求：
1. 前端可以启动。
2. 已登录才能访问业务页。
3. API 基础封装完整。
4. 只输出 frontend 文件。
第 14 段：登录页与认证状态
让前端先能进系统。

第十四轮任务：实现前端登录流程，只修改 frontend。

请实现：
1. 登录页
2. auth store
3. 调用：
   - POST /api/auth/login
   - GET /api/auth/me
4. 登录成功后保存 token
5. 刷新页面后自动恢复登录态
6. 未登录访问业务页时跳回登录页
7. 提供基础错误提示和加载态

要求：
- UI 简洁整洁
- 使用 Naive UI
- 只输出新增或修改的 frontend 文件
第 15 段：书架页
用户开始能看到书了。

第十五轮任务：实现前端书架页，只修改 frontend。

请实现：
1. 书架页展示书籍列表
2. 调用 GET /api/books
3. 支持按书名搜索
4. 支持上传 txt
5. 支持删除书籍
6. 支持点击进入书籍详情
7. 支持点击继续阅读

展示字段：
- 书名
- 作者
- 总章节数
- 总字数
- 最近阅读时间
- 阅读进度百分比
- 默认封面占位

要求：
1. 使用 Naive UI。
2. 页面在手机和桌面端都可用。
3. 上传后刷新列表。
4. 只输出新增或修改的 frontend 文件。
第 16 段：书籍详情页
把目录和规则挂上去。

第十六轮任务：实现前端书籍详情页，只修改 frontend。

请实现：
1. 调用 GET /api/books/{book_id}
2. 调用 GET /api/books/{book_id}/chapters
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

要求：
- UI 简洁
- 目录列表可点击跳转阅读页
- 只输出新增或修改的 frontend 文件
第 17 段：规则管理页
这个页面是你的差异化重点。

第十七轮任务：实现前端目录规则管理页，只修改 frontend。

请实现页面能力：
1. 获取规则列表：
   - GET /api/chapter-rules
2. 展示内置规则和自定义规则
3. 新增自定义规则
4. 编辑自定义规则
5. 删除自定义规则
6. 设置默认规则
7. 支持输入：
   - rule_name
   - regex_pattern
   - flags
   - description

要求：
1. 内置规则不可删除。
2. 使用表格 + 弹窗表单实现。
3. UI 使用 Naive UI。
4. 只输出新增或修改的 frontend 文件。
第 18 段：规则测试与预览
把“用户自定义正则”真正做实用。

第十八轮任务：在规则管理页中加入“测试规则”能力，只修改 frontend。

请实现：
1. 调用 POST /api/chapter-rules/test
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
5. 为 regex_pattern 输入框提供示例提示
6. 对错误正则显示友好报错

要求：
- 测试区可放在规则管理页中
- 只输出新增或修改的 frontend 文件
第 19 段：重新解析目录前端流程
把规则测试和书籍应用连接起来。

第十九轮任务：在前端实现“将规则用于某本书并重新解析”的交互，只修改 frontend。

请实现：
1. 在书籍详情页提供“重新解析目录”操作
2. 可选择目录规则
3. 调用 POST /api/books/{book_id}/reparse
4. 重新解析成功后刷新：
   - 书籍详情
   - 目录列表
5. 在规则管理页中也可选择一本书并快速应用某条规则进行重解析

要求：
- 交互要清晰
- 有加载态和成功/失败提示
- 只输出新增或修改的 frontend 文件
第 20 段：阅读页
这是使用频率最高的页面。

第二十轮任务：实现前端阅读页，只修改 frontend。

请实现：
1. 调用：
   - GET /api/books/{book_id}/chapters
   - GET /api/books/{book_id}/chapters/{chapter_index}
   - GET /api/books/{book_id}/progress
2. 页面打开时获取最新阅读进度并定位到对应章节
3. 阅读页支持：
   - 正文显示
   - 上一章 / 下一章
   - 当前章节标题
   - 当前进度展示
   - 字体大小调节
   - 行高调节
   - 浅色 / 深色主题
4. 设置项保存到 localStorage
5. 桌面端显示侧边目录
6. 手机端目录使用 Drawer

要求：
1. UI 整洁，适合阅读。
2. 正文区域排版舒适。
3. 只输出新增或修改的 frontend 文件。
第 21 段：阅读进度自动同步
把跨设备同步真正接上。

第二十一轮任务：在前端阅读页实现阅读进度自动同步，只修改 frontend。

请实现：
1. 调用 PUT /api/books/{book_id}/progress
2. 同步字段：
   - chapter_index
   - char_offset
   - percent
3. 同步策略：
   - 切换章节时立即保存
   - 阅读过程中节流保存，例如 15 秒一次
   - 页面关闭前尝试保存一次
4. 页面加载时优先使用服务端进度
5. percent 用于展示
6. 实际定位优先基于：
   - chapter_index
   - char_offset

要求：
1. 不要只靠总百分比定位。
2. 尽量避免频繁请求。
3. 只输出新增或修改的 frontend 文件。
第 22 段：前端收尾
最后统一修边角。

第二十二轮任务：对 frontend 做收尾整理，只修改 frontend。

请补充或完善：
1. 全局错误提示
2. 页面加载态
3. 空状态
4. API 类型定义整理
5. 组件抽离（如需要）
6. 响应式布局细节优化
7. 代码中明显重复逻辑的整理
8. README 中 frontend 启动说明

要求：
- 不要大改已有接口对接方式
- 以可运行、可联调为优先
- 只输出新增或修改的 frontend 文件
第 23 段：README、Docker、启动方式
最后交付工程化收口。

第二十三轮任务：生成项目交付文件。

请输出：
1. 根目录 README.md
2. backend/requirements.txt（如还未完善）
3. frontend/package.json（如需补充）
4. backend Dockerfile
5. frontend Dockerfile
6. docker-compose.yml
7. .gitignore
8. .env.example

README 要包含：
- 项目简介
- 技术栈
- 目录结构
- 本地开发启动方式
- Docker 启动方式
- 默认账号密码
- 目录规则功能说明
- 重新解析目录说明
- 阅读进度同步说明

要求：
- 内容完整
- 命令可执行
- 不要只给模板占位
第 24 段：联调与修复
这一步非常重要，专门用来逼 AI 修 bug。

第二十四轮任务：请你站在“联调与验收”的角度检查整个项目，列出并修复潜在问题。

请重点检查：
1. 前后端接口路径是否一致
2. 请求字段名是否一致
3. 返回结构是否一致
4. token 传递是否一致
5. chapter_rule_id 的使用是否一致
6. 阅读进度字段是否一致
7. 阅读页加载逻辑是否能正确恢复进度
8. 重新解析目录后页面是否正确刷新
9. 移动端目录抽屉是否正常工作
10. Docker 与本地启动命令是否一致可用

输出要求：
1. 先列出发现的问题
2. 再输出对应修复文件
3. 只输出新增或修改的文件
4. 不要空谈，要直接改代码


第二十五轮任务：仅对 frontend 的阅读正文页进行 UI 与前端交互重构。先分析项目结构，再给出修改计划，然后再改代码。

目标：
- 将当前后台卡片式阅读页重构为参考图2的沉浸式阅读体验
- 正文窄栏居中
- 顶部设置区不再常驻，改为点击“设置”后从左侧抽屉展开
- 左侧常驻目录取消，改为点击“目录”后从左侧抽屉展开
- 保留完整左侧工具栏
- 增加右侧悬浮操作区
- 保持滚动阅读
- 增加上一章 / 下一章按钮
- PC 端按钮默认显示
- 手机端按钮默认隐藏，点击屏幕后呼出

限制：
1. 仅修改 frontend
2. 不改 backend
3. 不改接口
4. 不改数据结构
5. 不改 Pinia store 字段含义
6. 保持现有阅读功能可用
7. 优先复用现有目录、设置、进度同步、主题切换、字体设置逻辑

具体要求：
- 左侧工具栏：桌面端固定显示，窄屏自动收起
- 目录：点击后从左侧抽屉展开
- 设置：点击后从左侧抽屉展开
- 顶部栏：不保留，做纯沉浸式
- 正文：窄栏居中、排版舒展
- 右侧悬浮区：桌面端固定显示，手机端收起
- 阅读进度：改为更简洁的进度条 / 百分比组件
- 顶部 / 底部按钮需真实可用
- 保持滚动阅读，增加上一章 / 下一章

输出要求：
1. 先分析阅读页相关文件、组件、状态、路由、样式
2. 再列出修改计划与涉及文件
3. 然后开始逐步修改代码
4. 最后给出验证清单


---

# 在线阅读与阅读3书源兼容实施计划

## 目标概述

在现有本地 TXT 阅读项目基础上，新增在线阅读能力，并通过多阶段演进，最终尽可能接近阅读3（Legado）原书源规则的高兼容支持。

本次实施必须遵守以下前提：

- 不破坏现有本地 TXT 阅读功能
- 在线阅读与本地 TXT 阅读解耦设计
- 不将在线书源逻辑直接硬塞进现有 TXT 解析链路
- 采用分阶段实施，不一次性追求高兼容
- 后端允许新增独立 `source engine / parser engine` 模块

---

## 当前目标分层

### 第一层目标：在线阅读基础版
实现最小在线阅读能力，使在线书籍可以完成：
- 搜索
- 详情
- 目录
- 正文
- 加入书架
- 进入阅读页

### 第二层目标：阅读3常见规则子集兼容
实现：
- 导入阅读3书源 JSON
- 支持常见规则能力
- 书源测试 / 调试能力

### 第三层目标：高兼容能力
逐步支持：
- 登录态
- Cookie
- 反爬
- JS 执行
- WebView 类规则或替代实现

---

## Phase 0：项目扫描与架构设计

### 任务目标
- 扫描现有前后端结构
- 明确可复用模块与必须新增模块
- 设计在线阅读接入方式
- 设计在线书籍与本地书籍共存方案

### 重点扫描内容

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

### 输出结果
- 项目扫描结果
- 数据流设计
- 模块拆分建议
- 风险点
- Phase 1 的最小落地范围

---

## Phase 1：最小在线阅读能力

### 目标
支持基础在线书源与公开网页书源，让在线书籍进入现有阅读流程。

### 后端建议新增模块
- `source_engine`
- `rule_parser`
- `source_importer`
- `source_validator`
- `online_book_service`
- `fetch_service`
- `content_parse_service`

### 前端建议新增入口
- 在线书源管理页
- 在线搜索入口
- 在线书籍详情页（如可复用则复用现有详情页）
- 书源测试入口（可后置到 Phase 2）

### 第一阶段建议支持能力
- GET / POST
- 基础 Header
- CSS / JSoup
- JSONPath
- XPath
- 正则
- 搜索 / 详情 / 目录 / 正文规则

### 第一阶段暂不支持
- JS 执行
- 登录态
- Cookie
- 复杂反爬
- WebView 类规则

### 第一阶段验收标准
- 能手动添加基础在线书源
- 能完成在线搜索、目录、正文抓取
- 在线书籍可进入现有书架 / 阅读页
- 不破坏本地 TXT 阅读

---

## Phase 2：阅读3常见规则子集兼容

### 目标
支持导入阅读3书源 JSON，并兼容常见规则组合。

### 重点任务
- 阅读3书源 JSON 字段映射
- 规则标准化
- 常见选择器与替换规则兼容
- 目录 / 详情 / 正文规则兼容
- 基础变量能力
- 书源测试 / 调试页

### 建议支持能力
- CSS / JSoup
- JSONPath
- XPath
- 正则
- 常见替换规则
- 目录倒序等高频规则

### 第二阶段验收标准
- 一批常见阅读3书源可导入
- 导入后可完成搜索 / 详情 / 目录 / 正文链路
- 调试工具可帮助定位规则失败原因

---

## Phase 3：高级兼容能力

### 目标
逐步支持阅读3高复杂度能力。

### 重点任务
- 登录态管理
- Cookie 管理
- 会话维持
- 更复杂 Header / 请求参数
- 反爬应对
- JS 执行能力
- WebView 类规则或等价替代方案

### 建议新增模块
- `session_handler`
- `cookie_store`
- `js_execution_sandbox`
- `anti_bot_handler`
- `webview_strategy`（或替代实现模块）

### 风险说明
此阶段是项目复杂度显著提升的阶段，必须单独控制风险：
- 安全风险
- 资源消耗
- 调试复杂度
- 可维护性下降
- 兼容率与稳定性冲突

### 第三阶段验收标准
- 高复杂度书源开始具备可用性
- 会话 / Cookie / 登录态有明确管理机制
- JS 执行具备隔离与超时控制
- 不影响基础在线阅读链路

---

## Phase 4：高兼容收尾

### 目标
提升阅读3原书源的整体兼容率与可用率。

### 重点任务
- 对导入书源进行兼容性回归
- 统计高频失败场景
- 补齐规则执行边界情况
- 完善调试信息与错误提示
- 提升导入成功率与实际可读率

### 第四阶段验收标准
- 常见高频书源兼容率提升
- 高频失败场景有明确解决方案
- 系统仍保持可维护性与可迭代性

---

## 可复用模块

预计优先复用：
- 现有书架能力
- 现有阅读页
- 现有阅读进度
- 现有阅读设置
- 现有部分详情页 / 书籍展示逻辑
- 现有 API / store / router 基础设施

---

## 必须新增模块

预计必须新增：
- 书源引擎
- 规则解析器
- 在线抓取服务
- 在线正文解析服务
- 书源导入器
- 书源校验器
- 书源调试能力
- 后期的会话 / Cookie / JS 执行 / 反爬 / WebView 相关模块

---

## 高风险点

1. 阅读3规则兼容本质上是规则执行引擎问题，不是普通页面功能扩展
2. JS 执行会显著抬高复杂度与安全风险
3. 登录态 / Cookie / 反爬 / WebView 会让系统从“内容抓取”升级为“复杂运行环境兼容”
4. 若过早追求高兼容，容易导致项目失控
5. 必须始终保证本地 TXT 阅读能力不被破坏

---

## 暂缓建议

以下能力不建议在第一阶段就做：

- JS 执行
- 登录态
- Cookie
- 复杂反爬
- WebView 类规则
- 高兼容阅读3原书源目标

原因：
- 风险高
- 调试复杂
- 对架构要求更高
- 不适合在最小在线阅读链路尚未稳定前进入

---

## 推荐执行顺序

1. 先完成 Phase 0 项目扫描与架构设计
2. 再进入 Phase 1 最小在线阅读能力
3. Phase 1 稳定后，再做 Phase 2 阅读3常见规则子集兼容
4. 最后再做 Phase 3 / Phase 4 高级兼容与兼容率提升