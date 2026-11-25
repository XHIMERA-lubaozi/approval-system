# 简易审批流系统

员工通过浏览器发起申请，由指定用户依次完成两级审批。项目采用 Vue 3、TypeScript、Vite、Django REST Framework、Simple JWT 和 PostgreSQL。

系统支持注册登录、草稿管理、提交、两级审批、驳回、待办和历史查询。可使用 Docker Compose 启动完整系统，也可单独运行数据库并在本机开发前后端。

## 已实现功能

- `POST /api/auth/register`：匿名注册；账号（`username`）唯一，使用 Django 密码哈希保存密码，成功返回 `201` 和用户摘要。
- `POST /api/auth/login`：匿名登录；使用 Django 认证校验凭据，成功返回 `{"access_token": "...", "token_type": "Bearer"}`。
- `GET /api/users/me`：通过 `Authorization: Bearer <JWT>` 获取当前用户，成功返回用户摘要。
- 统一错误结构 `{code, message, details?}`，覆盖参数校验、凭据错误、未认证、权限、404 与未预期异常。
- 通过 `LOGGING` 输出控制台日志；未预期异常记录一条 ERROR 日志，包含请求方法、路由、异常类型和脱敏后的堆栈。
- `GET /api/users`：返回审批人候选用户摘要；前端选择审批人时过滤当前账号。
- `POST /api/requests`：创建草稿；申请人取自当前用户，初始状态为 `draft`。
- `GET /api/requests`：查询“我的申请”或“待我审批”，支持状态、标题关键词、分页和总数。
- `GET /api/requests/{id}`：申请人和指定审批人查看详情及操作历史。
- `PUT /api/requests/{id}`：申请人完整更新自己的草稿。
- `DELETE /api/requests/{id}`：申请人删除自己的草稿。
- `POST /api/requests/{id}/submit`：申请人提交草稿，进入一级审批。
- `POST /api/requests/{id}/approve`、`POST /api/requests/{id}/reject`：当前审批人通过或驳回。
- `GET /api/requests/{id}/history`：申请人和指定审批人查询操作历史。
- 前端注册页、登录页、受保护首页、路由守卫、Bearer Token 注入、刷新恢复会话和退出登录。
- 前端提供“我的申请”和“待我审批”列表、草稿编辑、申请详情、审批操作与历史展示。

## Docker 一键启动

准备 Docker Desktop 或带 `docker compose` 的 Docker 环境。在项目根目录运行：

```sh
test -f .env || cp .env.example .env
docker compose up -d --build --wait
```

第一行仅在首次配置时需要。之后一条 `docker compose up -d --build --wait` 即可构建并启动全部服务。全新的本机演示环境也可直接使用 `docker compose --env-file .env.example up -d --build --wait`，后续操作继续使用相同的环境文件。有现存数据库卷时，应继续使用初始化该卷时的数据库凭据。

启动后打开 [http://localhost:8080](http://localhost:8080)。Nginx 提供 Vue 页面，并将同源 `/api` 请求转发给 Django。Django 等待 PostgreSQL 就绪并自动迁移，前端等待后端就绪后启动。

- `FRONTEND_PORT` 控制本机访问端口，默认 `8080`。PostgreSQL 的 `POSTGRES_PORT` 默认 `55432`，用于本机连接数据库，容器间连接使用 `db:5432`。
- `docker compose ps` 查看健康状态，`docker compose logs -f backend` 查看迁移和后端日志。
- `docker compose exec -T backend python manage.py test` 在容器中执行后端测试。前端类型检查由镜像构建执行。
- `docker compose down` 停止服务并保留 PostgreSQL 数据卷。示例环境变量用于本地开发或演示。

## 本机开发启动

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

## API 接口

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
| POST | `/api/requests/{id}/submit` | Bearer JWT | `200`，提交后的申请 |
| POST | `/api/requests/{id}/approve` | Bearer JWT | `200`，通过后的申请 |
| POST | `/api/requests/{id}/reject` | Bearer JWT | `200`，驳回后的申请 |
| GET | `/api/requests/{id}/history` | Bearer JWT | `200`，操作历史数组 |

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
- 列表 `scope` 默认为 `mine`，返回当前用户发起的申请。`scope=pending` 返回当前需要本人处理的申请。列表先筛选再分页，按创建时间和 ID 倒序，响应 `count` 为筛选后的总数。
- 创建、编辑、删除草稿均不写入审批历史；成功提交、通过和驳回分别写入一条记录，详情按时间及 ID 升序展示历史。

## 验证与停止

- 根目录运行 `docker compose config --quiet` 检查 Compose 配置，运行 `docker compose ps` 查看数据库状态。
- 在 `backend/` 运行 `uv run --locked python manage.py check` 检查 Django 配置，运行 `uv run --locked python manage.py test` 执行后端测试。
- 在 `frontend/` 运行 `npm run build` 执行前端类型检查和生产构建。
- 浏览器验收步骤、实际命令与结果见 [验收记录](doc/验收记录.md)。
- 在根目录运行 `docker compose down` 停止 Compose 服务。命名卷保留数据库数据。

## 目录与文档

- `frontend/` 存放浏览器页面、路由和 API 客户端。
- `backend/` 存放 Django 配置与 `users`、`approvals` 两个业务应用。
- `backend/common/exceptions.py` 和 `backend/common/logging.py` 提供统一异常处理与日志脱敏。
- `compose.yaml` 和 `.env.example` 提供本地数据库和后端配置入口。
- 需求、数据和接口分别见 [Spec](doc/Spec.md)、[ER 图](doc/ER图.md) 和 [OpenAPI](openapi.json)。
- 工程约定、技术决策和验收结果见 [开发规范](doc/开发规范.md)、[技术设计](doc/技术设计.md) 和 [验收记录](doc/验收记录.md)。
