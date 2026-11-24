# 简易审批流系统

员工通过浏览器发起申请，由指定用户依次完成两级审批。项目骨架采用 Vue 3、TypeScript、Vite、Django REST Framework 和 PostgreSQL。当前提供前后端启动入口、数据库配置与用户模型。注册、登录、申请和审批属于后续业务开发。

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

## 验证与停止

- 根目录运行 `docker compose config --quiet` 检查 Compose 配置，运行 `docker compose ps` 查看数据库状态。
- 在 `backend/` 运行 `uv run --locked python manage.py check` 检查 Django 配置，运行 `uv run --locked python manage.py test` 执行后端测试。脚手架阶段尚未加入业务测试。
- 在 `frontend/` 运行 `npm run build` 执行前端类型检查和生产构建。
- 在根目录运行 `docker compose down` 停止数据库。命名卷保留已有数据。

## 目录与文档

- `frontend/` 存放浏览器页面、路由和 API 客户端。
- `backend/` 存放 Django 配置与 `users`、`approvals` 两个业务应用。
- `compose.yaml` 和 `.env.example` 提供本地数据库和后端配置入口。
- 需求、数据和接口分别见 [Spec](doc/Spec.md)、[ER 图](doc/ER图.md) 和 [OpenAPI](openapi.json)。
- 工程约定和技术决策见 [开发规范](doc/开发规范.md) 和 [技术设计](doc/技术设计.md)。
