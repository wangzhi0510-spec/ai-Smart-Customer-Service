# 测试与验收

## 1. 测试层次

| 层次 | 目录/命令 | 目标 |
| --- | --- | --- |
| 后端单元 | `backend/tests` | 配置、认证、服务、RAG、错误协议 |
| 后端集成 | `backend/tests/integration` | Alembic、Milvus 生命周期、Compose 契约 |
| 后端 E2E | `backend/tests/e2e` | SQLAlchemy 文档 Worker 与 QAService 核心闭环 |
| 前端单元 | `frontend/tests` | Store、SSE 解析器、页面交互 |
| 浏览器 E2E | `frontend/tests/e2e` | 注册到删除后的真实浏览器流程 |
| RAG 评测 | `backend/evaluation` | 命中率、来源、fallback、延迟 |

## 2. 可重复命令

```powershell
.venv\Scripts\python.exe -m pytest -q
npm test --prefix frontend -- --run
npm run build --prefix frontend
frontend\node_modules\.bin\playwright.cmd test --config frontend/playwright.config.ts
.venv\Scripts\python.exe backend/evaluation/evaluate.py
docker compose config --quiet
docker compose --profile app config --quiet
git diff --check
```

集成测试可以单独运行：

```powershell
.venv\Scripts\python.exe -m pytest -m integration -q
```

当前已验证基线：后端 73 个测试通过，前端 10 个测试通过，Playwright 1 个核心流程通过，RAG 离线评测四个样例全部达到预期指标。

## 3. 核心验收路径

1. 注册或登录，确认 JWT 不出现在页面正文和日志。
2. 创建会话，上传 TXT/Markdown/PDF，确认返回 202 和 `pending`。
3. Worker 处理后确认状态变为 `ready`；无效文件确认 `failed` 和安全错误码。
4. 提问：先验证 FQA 命中，再验证 RAG 来源引用和无证据 fallback。
5. 用 `POST /api/v1/query/stream` 检查事件顺序 `start → delta/source* → done`。
6. 提交赞/踩，刷新历史确认反馈和来源持久化。
7. 删除文档后再次提问，确认不再检索旧来源。
8. 使用另一个用户 Token 访问文档、会话和消息，确认返回未授权或资源不存在。

## 4. 测试替身和外部依赖

单元和集成测试默认使用确定性 Fake Embedding、Fake Milvus、Fake Retrieval、Fake FQA 和 Fake LLM，不依赖网络、真实 API Key 或模型权重。Playwright 使用 API route mock 验证前端真实 DOM、路由和 SSE 契约；它不是对生产后端可用性的替代。

真实 MySQL、Redis、Milvus 和 DashScope 联调应在具备服务和密钥的环境中执行，并使用 `integration` 标记；测试日志不得包含文档正文、Prompt、Token 或密钥。

## 5. 失败诊断

- 首先运行失败测试的最小路径，不直接修改全量配置。
- 检查 `X-Request-ID`、稳定错误码和服务日志中的耗时/资源 ID。
- 外部 Provider 超时、Embedding/Milvus 不可用应返回受控错误并补偿配额。
- Playwright 失败时先检查浏览器控制台、SSE 响应和 API mock 契约。