# 部署与运行

## 1. 前置条件

- Windows、Linux 或 macOS，已安装 Docker Desktop/Engine、Docker Compose、Git。
- Python 3.12；Node.js 与 npm。
- 至少准备本地 `bge-m3` 和 `bge-reranker-large` 模型目录（真实 RAG 运行时需要）。
- DashScope API Key 仅在需要真实 LLM 时配置；测试可使用 Fake Provider。

## 2. 本地虚拟环境

```powershell
cd D:\code\codex_code\cs_rag_agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements-dev.txt
npm install --prefix frontend
```

Linux/macOS 将激活命令替换为 `source .venv/bin/activate`。`.venv/` 不提交 Git。

## 3. 环境变量

```powershell
Copy-Item .env.example .env
```

开发时至少设置：

- `DATABASE_URL`：本机 MySQL 连接串；
- `JWT_SECRET_KEY`：随机长字符串；
- `DOCUMENT_STORAGE_PATH`：文档持久化目录；
- `EMBEDDING_MODEL_PATH`、`RERANKER_MODEL_PATH`：本地模型路径；
- `DASHSCOPE_API_KEY`：真实 LLM 调用时填写。

`.env.example` 中秘密字段为空。不要把真实 `.env`、模型权重或上传文件提交仓库。

## 4. Docker Compose 双模式

仅启动基础设施：

```powershell
docker compose up -d mysql redis etcd minio milvus
docker compose ps
docker compose config --quiet
```

启动包含后端、Worker、前端的完整模式：

```powershell
docker compose --profile app up -d --build
docker compose --profile app ps
```

`backend` 容器启动命令会先执行 `alembic upgrade head`，随后启动 Uvicorn；`worker` 使用 documents 队列；前端容器监听 8080 并映射到 `${FRONTEND_PORT:-5173}`。

模型目录通过 `${MODEL_HOST_PATH:-./models}:/models:ro` 只读挂载，镜像构建不会复制模型。

## 5. 初始化数据库和 FQA

迁移命令：

```powershell
.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

初始化脚本用于创建兼容开发环境的表结构；生产和容器启动以 Alembic 为准：

```powershell
.venv\Scripts\python.exe backend\scripts\init_db.py
.venv\Scripts\python.exe backend\scripts\seed_fqa.py path\to\fqa.json
```

FQA JSON 为数组，每项至少包含 `question`、`answer`，可选 `user_id`、`similarity_threshold` 和 `is_active`。

## 6. 示例知识文档

仓库提供：

- `sample-data/product-faq.md`
- `sample-data/refund-policy.txt`
- `sample-data/account-guide.txt`

上传后通过 `GET /api/v1/documents` 轮询状态，直到 `ready`，再进行问答。

## 7. 服务地址

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://localhost:5173` |
| 后端 | `http://localhost:8000` |
| 存活检查 | `http://localhost:8000/api/v1/health/live` |
| Milvus | `localhost:19530` |
| MinIO API/控制台 | `localhost:9000` / `localhost:9001` |
| MySQL | `localhost:3306` |
| Redis | `localhost:6379` |

## 8. 停止与数据

```powershell
docker compose --profile app down
```

不带 `-v` 会保留命名卷。只有明确需要重建本地数据时才执行 `docker compose down -v`；该操作会删除 MySQL、Milvus、MinIO 等本地卷数据。