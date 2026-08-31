# AI 智能客服系统

基于 Vue 3、FastAPI、MySQL、Redis、Milvus 和大语言模型的企业智能客服系统。首版聚焦可验证核心闭环：认证、会话、知识库、FQA、混合检索 RAG、真实 POST-SSE、来源引用、反馈和 Docker 部署。

需求第一标准是《AI开发工程师笔试题.docx》；批准的工程化转换见[系统设计规格](docs/superpowers/specs/2026-08-28-AI智能客服系统设计文档.md)，执行清单见[任务清单](tasks/todo.md)。

## 核心流程

```text
注册/登录 → 创建会话 → 上传 TXT/MD/PDF → 异步解析与向量化
→ FQA 优先 → Dense + Sparse → RRF → 父块回收 → 重排
→ 证据型 Prompt → qwen-plus → POST-SSE → 来源/历史/反馈
```

## 快速开始

### 1. 创建环境

```powershell
cd D:\code\codex_code\cs_rag_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
npm install --prefix frontend
Copy-Item .env.example .env
```

填写本地数据库、JWT 密钥；真实 RAG 运行时再配置模型目录和 DashScope API Key。秘密、模型权重和用户文件不会提交 Git。

### 2. 启动基础设施

```powershell
docker compose up -d mysql redis etcd minio milvus
```

启动完整 app profile：

```powershell
docker compose --profile app up -d --build
```

### 3. 启动后端/前端（非容器开发模式）

```powershell
.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
npm run dev --prefix frontend -- --host 127.0.0.1 --port 5173
```

浏览器访问 `http://localhost:5173`；后端存活检查为 `http://localhost:8000/api/v1/health/live`。

## 常用验证

```powershell
.venv\Scripts\python.exe -m pytest -q
npm test --prefix frontend -- --run
npm run build --prefix frontend
frontend\node_modules\.bin\playwright.cmd test --config frontend/playwright.config.ts
.venv\Scripts\python.exe backend\evaluation\evaluate.py
docker compose config --quiet
docker compose --profile app config --quiet
git diff --check
```

## 文档导航

- [项目总览](docs/project-overview.md)
- [API 契约](docs/api.md)
- [数据库设计](docs/database.md)
- [AI 架构与 RAG](docs/ai-architecture.md)
- [业务流程](docs/business-flow.md)
- [部署与运行](docs/deployment.md)
- [测试与验收](docs/testing.md)
- [AI 使用与人工审查](docs/ai-usage.md)
- [Agent 挑战题设计](docs/agent-challenge.md)
- [后端说明](backend/README.md)
- [前端说明](frontend/README.md)

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router
- 后端：Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic
- 基础设施：MySQL 8.4、Redis 7.4、Milvus 2.4、etcd、MinIO、Celery
- AI：本地 bge-m3、bge-reranker-large、DashScope qwen-plus
- 测试：pytest、Vitest、Playwright

## 首版边界

图片识别、追问建议、多知识库路由、HyDE、SubQuery、Backtracking、RAGAS 和多微服务代码修改 Agent 属于第二阶段。首版保留真实接口边界和文档设计，不把未实现能力描述为已完成。

## 安全原则

- `.env`、真实 API Key、JWT 密钥、数据库密码、模型权重、用户上传文件、日志和构建产物禁止提交。
- 所有资源按 JWT 当前用户隔离；密码使用 Argon2id。
- 日志不记录密码、Token、Prompt、文档正文或 API Key。
- 外部系统通过 Adapter 注入，测试使用确定性 Fake。