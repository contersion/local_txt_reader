# TXT Reader

TXT Reader 是一个面向个人使用场景的 TXT 在线阅读器，支持上传本地 TXT 文件、自动解析章节、管理书架、同步阅读进度，以及按自己的文本格式定制章节识别规则。

当前版本：`v1.01`

这一版主要围绕两个方向做了完善：

- 书籍详情页的目录展示从“页面内整段展开”调整为“查看目录”按钮触发弹窗 / 抽屉，长目录书籍的浏览体验更清爽。
- 后端在 `DEBUG=false` 时会自动关闭 Swagger UI 与 OpenAPI 文档端点，避免生产环境继续暴露调试文档入口。

当前仓库采用轻量前后端分离架构：

- 前端：Vue 3 + Vite + TypeScript + Vue Router + Pinia + Naive UI
- 后端：FastAPI + SQLAlchemy + SQLite
- 部署方式：Docker Compose

本 README 基于当前仓库真实结构编写，只保留源码目录和关键运行目录，不展开 `node_modules`、`dist`、`.venv` 之类的生成产物目录。

开发过程及思路见 [`development-process.md`](./development-process.md)。

## 使用方法

推荐使用流程如下：

1. 使用默认账号登录系统。
2. 在书架页上传 `.txt` 文件。
3. 如果默认章节规则识别不理想，到“目录规则”页测试或新建自定义规则。
4. 在书籍详情页通过“查看目录”按钮打开目录弹层，浏览章节、切换章节规则并重新解析。
5. 进入阅读页继续阅读，系统会按 `chapter_index + char_offset` 同步进度。
6. 根据需要调整字体大小、行高、字间距、段间距、阅读宽度、主题，并在不同设备间同步这些偏好与书架筛选状态。

## 通过 Docker Compose 部署

本项目当前**推荐且明确支持**的部署方式是 **Docker Compose**，适合本地运行、家庭服务器以及轻量自托管场景。

### 运行前准备

开始前请确认你的环境已满足以下条件：

* 已安装 Docker Desktop，或已安装 Docker Engine
* 已启用 Docker Compose

### 1. 获取项目源码

先克隆仓库并进入项目目录：

```bash
git clone https://github.com/contersion/local_txt_reader.git
cd local_txt_reader
```

### 2. 准备环境变量

在项目根目录复制一份环境变量文件：

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

如需修改端口、默认账号、密钥或调试行为，请编辑根目录下生成的 `.env` 文件。

常用配置项包括：

* `BACKEND_PORT`：宿主机后端端口，默认 `8000`
* `FRONTEND_PORT`：宿主机前端端口，默认 `24412`
* `VITE_API_BASE_URL`：前端构建时使用的 API 地址
* `CORS_ORIGINS`：允许访问后端的浏览器来源
* `SECRET_KEY`：后端签名密钥
* `DEFAULT_ADMIN_USERNAME`：默认管理员用户名
* `DEFAULT_ADMIN_PASSWORD`：默认管理员密码
* `DEBUG`：后端调试开关，同时影响 Swagger / OpenAPI 文档是否开放

如果你修改了前后端端口，建议同时检查 `VITE_API_BASE_URL` 和 `CORS_ORIGINS`，以避免前端仍访问旧地址。

在大多数 Docker 部署场景下，建议保持 `VITE_API_BASE_URL` 为空，让前端通过同源 `/api` 转发访问后端，这样在局域网、公网或反向代理场景下会更省心。

### 3. 启动服务

首次启动，或在更新代码、依赖后，建议执行：

```bash
docker compose up --build -d
```

如果只是日常启动已有服务，直接执行：

```bash
docker compose up -d
```

### 4. 初始化说明

首次启动时，后端会自动完成以下初始化操作：

* 创建 `backend/data/` 数据目录
* 创建 `backend/uploads/` 上传目录
* 初始化 SQLite 数据库
* 创建所有数据表
* 写入内置章节规则
* 创建默认管理员账号
* 为已有用户补齐默认书架分组

首次初始化时，系统会自动写入一个默认管理员：

- 用户名：`admin`
- 密码：`admin123`

如需修改，请在第一次启动前编辑项目根目录 `.env` 中的：

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

注意：

- 这两个值只会在“默认管理员尚不存在”时生效。
- 如果数据库已经初始化过，单纯修改 `.env` 不会自动重置已有账号密码。
- 当前 SQLite 数据库默认保存在 `backend/data/app.db`。如果你是本地测试环境，且确认可以清空已有数据，可以删除该数据库后重新执行 `docker compose up --build -d` 让系统重新初始化。

**如何维护默认管理员账号**

如果数据库里已经存在默认管理员，单纯修改 `.env` 中的 `DEFAULT_ADMIN_USERNAME` 或 `DEFAULT_ADMIN_PASSWORD`，都不会自动改写已有管理员记录。应用启动时也不会替你把旧管理员自动改名；这类操作需要手动运行维护脚本。

当前推荐使用：

```bash
python scripts/manage_admin_user.py
```

Docker 部署场景可以直接执行：

```bash
docker compose exec backend python scripts/manage_admin_user.py
```

**重置当前默认管理员密码**

如果数据库中已经存在 `DEFAULT_ADMIN_USERNAME`，脚本会执行 `reset password`：

```bash
docker compose exec backend python scripts/manage_admin_user.py --password "new-password"
```

如果不显式传参，脚本会默认读取当前配置中的：

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

**将旧默认管理员改名为新用户名**

如果数据库中不存在当前 `DEFAULT_ADMIN_USERNAME`，但仍存在旧默认管理员（例如 `admin`），脚本会执行 `rename admin`，把旧管理员改名为新用户名，并同步更新密码。

最常见的做法是先在 `.env` 中改好：

- `DEFAULT_ADMIN_USERNAME=contersion`
- `DEFAULT_ADMIN_PASSWORD=your-new-password`

然后执行：

```bash
docker compose exec backend python scripts/manage_admin_user.py
```

如果你希望显式指定旧用户名、新用户名和密码，也可以执行：

```bash
docker compose exec backend python scripts/manage_admin_user.py --old-username admin --new-username contersion --password "new-password"
```

本地直接运行后端时，同样适用：

```bash
python scripts/manage_admin_user.py --old-username admin --new-username contersion --password "new-password"
```

脚本行为说明：

- 默认读取当前配置中的 `DEFAULT_ADMIN_USERNAME` 和 `DEFAULT_ADMIN_PASSWORD`
- `--old-username` 和 `--new-username` 用于显式执行管理员改名
- `--password` 的优先级高于 `.env` / 当前环境变量
- 如果数据库中已存在当前 `DEFAULT_ADMIN_USERNAME`，脚本只会重置该用户密码
- 如果当前默认管理员不存在，但旧默认管理员 `admin` 存在，脚本会尝试把 `admin` 改名为新的默认管理员用户名
- 如果 `new_username` 已存在，脚本不会直接覆盖，而是明确报错提示
- 如果旧用户名和新用户名都不存在，脚本会明确提示，不会盲目新增多个管理员
- 脚本只在你手动执行时生效，不会在应用启动时自动改名

### 5. 访问地址

服务启动后，可通过以下地址访问：

* 前端页面：`http://localhost:24412`
* 后端接口：`http://localhost:8000`
* 健康检查：`http://localhost:8000/health`
* Swagger 文档：`http://localhost:8000/docs`（仅在 `DEBUG=true` 时可用）

如果你修改了端口，请将上面的地址替换为实际配置值。

### 6. 常用命令

查看服务日志：

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

停止服务：

```bash
docker compose down
```

重新构建并启动：

```bash
docker compose up --build -d
```




## API 文档与调试说明

`http://127.0.0.1:8000/docs` 对应的是 FastAPI 自动生成的 Swagger UI。它主要用于：

- 查看所有后端接口、参数、返回结构
- 直接在浏览器中调接口做测试
- 方便前后端联调和排错

当前版本中，接口文档端点的行为已经和 `DEBUG` 开关绑定：

- `DEBUG=true` 时，以下端点可访问：
  - `/docs`
  - `/redoc`
  - `/openapi.json`
- `DEBUG=false` 时，以上端点会自动关闭

这次修复解决了“即使在 `DEBUG=false` 情况下，Swagger UI 和 OpenAPI 文档端点仍然可访问”的问题。

生产环境建议：

- 使用 `DEBUG=false`
- 不对公网暴露调试文档入口
- 同时修改默认 `SECRET_KEY`
- 不要继续使用默认管理员密码

## 目录结构

下面是当前仓库中与开发和运行直接相关的真实结构：

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ core/             # 配置、数据库、依赖、鉴权、异常处理
│  │  ├─ models/           # SQLAlchemy 模型
│  │  ├─ routers/          # FastAPI 路由
│  │  ├─ schemas/          # Pydantic 数据结构
│  │  ├─ services/         # 业务逻辑
│  │  ├─ utils/            # 编码、正则、文件等工具
│  │  ├─ init_data.py      # 初始化建库与种子数据
│  │  └─ main.py           # 后端入口
│  ├─ tests/               # 后端测试
│  ├─ scripts/             # 运维/维护脚本，如默认管理员维护
│  ├─ data/                # SQLite 数据目录（运行期）
│  ├─ uploads/             # TXT 原始文件与标准化文本（运行期）
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ README.md
├─ frontend/
│  ├─ src/
│  │  ├─ api/              # 前端 API 请求封装
│  │  ├─ components/       # 通用组件与弹窗
│  │  ├─ layouts/          # 应用布局
│  │  ├─ pages/            # 登录、书架、详情、阅读、规则管理页面
│  │  ├─ router/           # 路由与鉴权守卫
│  │  ├─ stores/           # Pinia 状态
│  │  ├─ styles/           # 全局样式
│  │  ├─ types/            # 前后端类型定义
│  │  ├─ utils/            # token、格式化等工具
│  │  └─ main.ts           # 前端入口
│  ├─ Dockerfile
│  ├─ nginx.conf
│  ├─ package.json
│  └─ README.md
├─ docs/
│  └─ IMPLEMENTATION_STEPS.md
├─ docker-compose.yml
├─ .env.example
├─ UPDATE.md
└─ README.md
```

## 功能说明

### 1. 登录与认证

- 后端提供 `POST /api/auth/login` 和 `GET /api/auth/me`
- 前端登录态由 Pinia 管理，并把 token 保存在浏览器 `localStorage`
- 刷新页面后会自动恢复登录态
- 未登录状态下访问业务页会被路由守卫重定向到登录页

### 2. 书架

- 展示当前用户书籍列表
- 支持按书名搜索
- 支持上传 TXT
- 支持删除书籍
- 支持显示最近阅读时间和阅读百分比
- 支持继续阅读
- 支持为书籍分配分组

书架分组是当前仓库中的真实功能，不是占位设计：

- 可以创建、重命名、删除分组
- 系统会自动维护默认分组
- 书籍至少保留一个分组，避免出现“无分组书籍”

### 3. TXT 上传与章节解析

- 仅支持上传 `.txt` 文件
- 原始文件会保存到本地磁盘
- 后端会检测编码并尽量兼容：
  - `UTF-8`
  - `GBK`
  - `UTF-16`
- 标准化后的正文会按 UTF-8 保存
- 上传后会立即按当前规则解析章节并写入数据库

如果没有匹配到任何章节，系统不会报错中断，而是自动降级为“全文单章节模式”，保证书仍然可读。

### 4. 书籍详情与目录交互

当前版本中，书籍详情页的目录展示方式已经做了交互优化：

- 详情页不再默认整页展开完整目录列表
- 目录改为通过“查看目录”按钮触发弹窗 / 抽屉显示
- 用户可以在弹层中滚动浏览目录，并直接点击章节跳转到阅读页
- 原先用于解释目录入口的说明卡片 / 注释区域已经移除，详情页主体更简洁
- 对于章节很多的书籍，详情页不再被长目录拉长，信息密度与可读性都更好

书籍详情页仍然保留：

- 书名、作者、文件信息、编码、总章节数、总字数
- 当前使用的章节规则
- 切换规则并重新解析整本书的入口

### 5. 目录规则管理

当前仓库已经实现完整的规则管理链路：

- 查看内置规则和自定义规则
- 新增、编辑、删除自定义规则
- 设置默认规则
- 测试规则是否能命中文本
- 直接把某条规则应用到某本书并触发重新解析

内置规则至少包含：

- 中文章节规则
- 英文章节规则
- 卷章混合规则
- 单章节全文模式

### 6. 阅读页

阅读页是目前前端里实现最完整的业务页面之一，支持：

- 按章节加载正文，而不是整本书一次性返回
- 上一章 / 下一章切换
- 目录抽屉
- 设置抽屉
- 沉浸式阅读布局
- PC 与移动端响应式适配

### 7. 阅读进度同步

进度同步的真实逻辑是：

- 以 `chapter_index + char_offset` 为主
- `percent` 主要用于展示
- 切换章节时立即保存
- 阅读过程中按节流策略自动同步
- 页面关闭前尝试再次保存

后端在进度冲突时会优先保留 `updated_at` 更新更晚的记录。

## 个性化调整

### 1. 自定义章节识别规则

这是项目最核心的个性化能力之一。

你可以：

- 自定义正则表达式
- 自定义 flags，例如 `MULTILINE`、`IGNORECASE`
- 在规则管理页直接测试真实匹配结果
- 将规则设为默认规则
- 将规则应用到某一本书并立即重解析

这意味着不同来源、不同排版风格的 TXT 小说，都可以根据自己的标题格式定制解析逻辑。

### 2. 阅读偏好

阅读页当前支持以下个性化设置：

- 字体大小
- 行高
- 字间距
- 段间距
- 阅读宽度
- 浅色 / 深色主题

这些设置现在会同步保存到后端用户偏好中：

- 登录后优先读取账号已保存的阅读设置
- 如果服务端还没有旧用户偏好，会兼容导入浏览器里已有的旧 `localStorage` 阅读设置
- 同一账号在不同设备登录后，会恢复相同的阅读展示设置

作为兼容兜底，前端仍会保留本地缓存，但账号级服务端偏好已经成为主数据源。

### 3. 书架整理方式

除了阅读设置，项目还支持按分组整理书架：

- 自定义分组名称
- 为同一本书分配多个分组
- 在书架页按分组筛选

当前版本还会同步书架页的个人浏览状态：

- 排序方式
- 搜索条件
- 当前分组
- 为后续分页能力预留的页码 / pageSize 偏好字段

因此从书籍详情页或阅读页返回书架后，书架不会再回到默认排序或清空筛选条件；同一账号换设备后，也会恢复上次保存的书架筛选状态。

这更偏向“书架组织方式”的个性化，而不是阅读器样式个性化。

## 常见问题

### 1. 启动后无法访问前端或后端

先检查容器是否正常运行：

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

默认访问地址是：

- 前端：`http://localhost:24412`
- 后端：`http://localhost:8000`

如果你修改了端口，请确认 `.env` 中的：

- `BACKEND_PORT`
- `FRONTEND_PORT`
- `VITE_API_BASE_URL`
- `CORS_ORIGINS`

是一致的。

### 2. 为什么修改了默认账号密码，登录还是旧账号？

因为默认账号只在“数据库里还没有这个用户”时写入一次。

如果 `backend/data/app.db` 已经存在并且管理员已创建，修改 `.env` 不会自动覆盖旧账号。

### 3. 上传 TXT 后没有识别出目录怎么办？

这是预期内可恢复的情况。

系统会自动降级为“全文”单章节模式，保证可以继续阅读。之后你可以：

- 到“目录规则”页测试现有规则
- 新建自定义规则
- 回到书籍详情页重新解析目录

### 4. 为什么某些 TXT 会提示编码不支持？

当前真实实现主要支持：

- UTF-8
- GBK
- UTF-16

如果文件使用了其他编码，后端会直接返回友好错误，而不会错误入库。

### 5. 为什么分组删不掉？

如果某个分组下有书籍只属于这一个分组，后端会阻止删除，避免书籍变成“完全没有分组”的状态。

### 6. 阅读设置会不会跨设备同步？

会。

当前仓库里：

- 阅读进度会同步到后端
- 阅读样式偏好会同步到后端用户偏好
- 书架排序、搜索条件、当前分组等状态也会同步到后端用户偏好

所以换设备后，阅读位置可以恢复，字体大小、行高、字间距、段间距、阅读宽度、主题，以及书架筛选状态也会自动恢复。

### 7. 为什么 `DEBUG=false` 时访问不了 `/docs`？

这是当前版本的预期行为。

为了避免在非调试环境继续暴露接口文档入口，以下端点会在 `DEBUG=false` 时自动关闭：

- `/docs`
- `/redoc`
- `/openapi.json`

如果你是在本地开发、联调或排错，需要重新打开接口文档，可以把项目根目录 `.env` 中的 `DEBUG` 改成 `true`，然后重启后端服务。

### 8. 为什么前端默认端口改成了 `24412`？

这是一次真实部署后的兼容性调整。

在当前 Windows + Docker Desktop + IPv6 DDNS 的部署环境里，项目原本使用的前端默认端口 `5173` 可以在本机正常访问，但蜂窝网络下的外网访问表现不稳定；切换到高位端口 `24412` 后，前端入口恢复正常。因此当前仓库把 `24412` 作为默认前端入口端口。

因为前端已经通过同源 `/api` 代理到后端，所以实际对外优先只需要开放前端端口 `24412`；后端 `8000` 更适合保留给本机调试、内网或受控环境使用。

## 后续扩展建议

结合当前真实仓库结构，比较自然的下一步扩展方向有：

### 1. 增加前端自动化测试

目前后端测试已经比较完整，前端更偏真实页面实现和手动联调。可以考虑补充：

- 关键页面的组件测试
- 登录、上传、阅读链路的端到端测试
- Docker 部署后的 smoke test

### 2. 增强书籍元数据管理

当前书籍上传后，标题主要来自文件名，作者和描述默认较弱。可以继续补：

- 编辑作者
- 编辑简介
- 自定义封面
- 最近阅读排序 / 分组排序

### 3. 增强阅读器能力

当前阅读器已具备核心能力，但还可以继续扩展：

- 更多主题方案
- 段落间距和页边距设置
- 目录搜索
- 阅读统计
- 书签 / 批注

### 4. 增加数据备份与迁移能力

项目当前使用 SQLite 和本地上传目录，很适合做个人数据备份。后续可以考虑：

- 导出数据库与上传文件
- 导入备份
- 迁移到新机器

### 5. 明确依赖版本与交付边界

当前仓库已有 Docker 化部署能力，但还可以进一步增强可维护性：

- 增加更严格的依赖锁定策略
- 增加发布说明
- 增加升级与数据兼容说明

## 补充说明

- 后端还有单独的快速说明文档：[`backend/README.md`](./backend/README.md)
- 前端还有单独的说明文档：[`frontend/README.md`](./frontend/README.md)
- 开发过程文档在：[`docs/IMPLEMENTATION_STEPS.md`](./docs/IMPLEMENTATION_STEPS.md)
- 当前版本更新说明见：[`UPDATE.md`](./UPDATE.md)
