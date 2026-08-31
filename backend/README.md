# Backend

FastAPI 后端负责认证、会话、文档、问答、SSE 和异步文档入库。

## 本地运行

```powershell
cd D:\code\codex_code\cs_rag_agent
.venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

环境变量从仓库根目录 `.env` 读取，模板为 `.env.example`。开发测试默认可以使用 SQLite/Fake 依赖；真实 RAG 需要 MySQL、Redis、Milvus、本地模型和 DashScope Key。

## 目录

- `app/api`：路由、SSE 序列化和错误处理
- `app/services`：业务编排和资源归属校验
- `app/models`、`app/schemas`：数据库模型与 Pydantic 契约
- `app/rag`：解析、清洗、切块、检索、上下文和 Prompt
- `app/adapters`：文件、Redis、Milvus、Embedding、重排和 LLM 边界
- `app/workers`：Celery 文档处理任务
- `migrations`：Alembic 迁移
- `tests`：单元、集成和 E2E 测试

## 常用命令

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest -m integration -q
.venv\Scripts\python.exe backend\evaluation\evaluate.py
```

## 设计约束

- API 不直接访问数据库或模型，统一经过 Service/Adapter 边界。
- 用户资源按 JWT subject 隔离。
- 所有业务主键为 UUID，时间按 UTC 保存。
- 错误返回稳定错误码，日志不包含密码、Token、Prompt、文档正文或 API Key。
- 数据库结构只能通过 Alembic 迁移变更。