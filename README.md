# 简易审批流系统

员工通过浏览器发起申请，由指定用户依次完成两级审批。项目采用 Vue 3、TypeScript、Vite、Django REST Framework、Simple JWT 和 PostgreSQL。

当前迭代已完成用户注册、登录、获取当前用户、审批人候选列表，以及草稿的创建、列表、详情、编辑和删除，包含浏览器端登录闭环、统一异常处理和日志脱敏。提交、两级审批和审批历史属于后续阶段。

## 已实现功能

- `POST /api/auth/register`：匿名注册；账号（`username`）唯一，使用 Django 密码哈希保存密码，成功返回 `201` 和用户摘要。
- `POST /api/auth/login`：匿名登录；使用 Django 认证校验凭据，成功返回 `{"access_token": "...", "token_type": "Bearer"}`。
- `GET /api/users/me`：通过 `Authorization: Bearer <JWT>` 获取当前用户，成功返回用户摘要。
- 统一错误结构 `{code, message, details?}`，覆盖参数校验、凭据错误、未认证、权限、404 与未预期异常。
- 通过 `LOGGING` 输出控制台日志；未预期异常记录一条 ERROR 日志，包含请求方法、路由、异常类型和脱敏后的堆栈。
- `GET /api/users`：返回审批人候选用户摘要；前端选择审批人时过滤当前账号。
- `POST /api/requests`：创建草稿；申请人取自当前用户，初始状态为 `draft`。
- `GET /api/requests`：查询“我的申请”列表，支持状态、标题关键词、分页和总数。
- `GET /api/requests/{id}`：申请人和指定审批人查看详情，草稿 `history` 为空数组。
- `PUT /api/requests/{id}`：申请人完整更新自己的草稿。
- `DELETE /api/requests/{id}`：申请人删除自己的草稿。
- 前端注册页、登录页、受保护首页、路由守卫、Bearer Token 注入、刷新恢复会话和退出登录。
- 前端“我的申请”列表、新建/编辑表单、详情页、删除确认、筛选、搜索和分页。

## 本地启动

准备 Docker Desktop 或支持 Docker Compose 的 Docker 环境、Node.js 22.12+、Python 3.13 和 uv。以下命令以项目根目录为起点。

1. 配置环境并启动 PostgreSQL。

   ```sh
   test -f .env || cp .env.example .env
   docker compose up -d --wait db
   ```

   `.env` 中的 `POSTGRES_PORT` 是本机映射端口，默认 `55432`。端口已被占用时可调整该值。示例密码和密钥仅用于本地开发。共享环境使用独立的随机值。

2. 在后端终端安装依赖、执行迁移并启动 Django。

   ```sh
   cd backend
   uv sync --locked
   uv run --locked python manage.py migrate
   uv run --locked python manage.py runserver 127.0.0.1:8000
   ```

3. 在另一个终端安装依赖并启动前端。

   ```sh
   cd frontend
   npm ci
   npm run dev
   ```

   打开 [前端](http://127.0.0.1:5173/)。Vite 在本地将 `/api` 请求代理到 Django。

## 认证与草稿接口

| 方法 | 路由 | 认证 | 成功响应 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 匿名 | `201`，`{id, username, display_name}` |
| POST | `/api/auth/login` | 匿名 | `200`，`{access_token, token_type}` |
| GET | `/api/users/me` | Bearer JWT | `200`，`{id, username, display_name}` |
| GET | `/api/users` | Bearer JWT | `200`，用户摘要数组 |
| POST | `/api/requests` | Bearer JWT | `201`，创建后的草稿 |
| GET | `/api/requests` | Bearer JWT | `200`，`{count, page, page_size, results}` |
| GET | `/api/requests/{id}` | Bearer JWT | `200`，申请详情 |
| PUT | `/api/requests/{id}` | Bearer JWT | `200`，更新后的草稿 |
| DELETE | `/api/requests/{id}` | Bearer JWT | `204`，无响应体 |

- 注册字段：`username`、`password`、`display_name` 均必填。账号（`username`）最长 150，仅允许 Unicode 字母、数字及 `@ . + - _`；昵称（`display_name`）最长 150；密码至少 8 位，包含大写字母、小写字母、数字、符号中的至少两类，并通过项目配置的 Django 密码校验。
- 账号重复返回 `400`，`details.username` 包含可展示的字段错误；数据库唯一约束覆盖并发注册。
- 账号不存在或密码错误统一返回 `400`，`code` 为 `invalid_credentials`，`message` 为“账号或密码错误”。
- 缺少、无效或过期 Token 返回 `401`，`code` 为 `unauthorized`。
- 访问令牌只保存在浏览器 `sessionStorage`。刷新页面时若存在 Token，前端调用 `/api/users/me` 恢复用户；受保护请求返回 `401` 时清除本地会话并跳转登录页。
- 本轮不包含刷新令牌、服务端注销、邮件验证、找回密码、第三方登录或管理员角色。

### 草稿规则

- 申请单包含标题、内容、状态、申请人、两级审批人、当前步骤、创建/更新/提交时间；当前审批人按状态和步骤计算。
- 新建和编辑只接收 `title`、`content`、`first_approver_id`、`second_approver_id`。标题最长 100、内容最长 2000，且不能仅含空白。
- 两级审批人必须存在且不能是申请人，允许同一用户担任两级审批人。
- 创建时状态固定为 `draft`，当前步骤、当前审批人和提交时间为空；编辑成功更新 `updated_at`。
- 申请人或任一指定审批人可查看详情；只有申请人可编辑或删除自己的草稿，且仅限草稿。
- 列表 `scope` 默认为 `mine`，仅返回当前用户发起的申请；`scope=pending` 本轮返回 `400`。列表先筛选再分页，按创建时间和 ID 倒序，响应 `count` 为筛选后的总数。
- 本轮创建、编辑、删除草稿均不写入审批历史；详情的 `history` 固定为空数组。

## 验证与停止

- 根目录运行 `docker compose config --quiet` 检查 Compose 配置，运行 `docker compose ps` 查看数据库状态。
- 在 `backend/` 运行 `uv run --locked python manage.py check` 检查 Django 配置，运行 `uv run --locked python manage.py test` 执行后端测试。当前 47 项测试覆盖注册、登录、Token 场景、统一异常与日志脱敏，以及草稿校验、审批人规则、权限、列表范围、筛选分页、更新和删除。
- 在 `frontend/` 运行 `npm run build` 执行前端类型检查和生产构建。
- 浏览器验收步骤、实际命令与结果见 [验收记录](doc/验收记录.md)。
- 在根目录运行 `docker compose down` 停止数据库。命名卷保留已有数据。

## 目录与文档

- `frontend/` 存放浏览器页面、路由和 API 客户端。
- `backend/` 存放 Django 配置与 `users`、`approvals` 两个业务应用。
- `backend/common/exceptions.py` 和 `backend/common/logging.py` 提供统一异常处理与日志脱敏。
- `compose.yaml` 和 `.env.example` 提供本地数据库和后端配置入口。
- 需求、数据和接口分别见 [Spec](doc/Spec.md)、[ER 图](doc/ER图.md) 和 [OpenAPI](openapi.json)。
- 工程约定、技术决策和验收结果见 [开发规范](doc/开发规范.md)、[技术设计](doc/技术设计.md) 和 [验收记录](doc/验收记录.md)。
