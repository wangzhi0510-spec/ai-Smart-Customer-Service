# AI 智能客服系统实施计划

> **面向 Agent 的执行提示：** 实施本计划时必须按任务逐项执行。每个任务先写失败测试，再写最小实现，测试通过后提交；不得跳过验收步骤。必要时使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans`。

**目标：** 根据已批准的中文设计规格，构建可运行、可测试、可 Docker 部署并可上传 GitHub 的 AI 智能客服核心闭环。

**架构：** Vue 3 + TypeScript 前端通过 REST 和 POST-SSE 访问 FastAPI。后端按 API、Service、Repository、Adapter、RAG 分层，MySQL 保存业务数据，Redis 提供缓存、配额和 Celery 队列，Milvus 保存 bge-m3 文档向量，独立 Worker 负责异步入库。

**技术栈：** Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、MySQL 8、Redis 7、Celery 5、Milvus standalone、bge-m3、bge-reranker-large、DashScope qwen-plus、Vue 3、TypeScript、Vite、Pinia、Vitest、Playwright、Docker Compose。

**规格文档：** `docs/superpowers/specs/2026-08-28-AI智能客服系统设计文档.md`

## 全局约束

- 原始《AI开发工程师笔试题.docx》是第一标准；优化不能削弱原文验收目标。
- 首版实现核心闭环；HyDE、子查询、回溯检索、图片识别、追问、后台和 Agent 只预留接口。
- 默认 LLM 为 DashScope `qwen-plus` OpenAI 兼容接口；测试使用 Mock Provider。
- 支持手机号或邮箱注册登录；密码使用 Argon2id；接口使用 JWT access token。
- 单问题不超过 500 字符；默认每用户每日 100 次问答。
- 文档支持 `.txt`、`.md`、`.pdf`；默认单文件 20 MiB；状态为 `pending/processing/ready/failed`。
- Embedding 使用本地 `bge-m3`，重排使用 `bge-reranker-large`；模型路径从环境变量读取并挂载，不打入镜像。
- RAG 首版必须包含 Dense + Sparse 检索、RRF、父块回收、重排、来源引用、版本控制和长文档防遗漏策略。
- 流式接口为 `POST /api/v1/query/stream`，返回标准 SSE `start/delta/source/done/error` 事件，禁止逐字符模拟。
- 真实 `.env`、模型、上传文件、缓存、日志、数据库和构建产物不得提交 Git。
- 每个任务完成后必须运行该任务的测试，使用规范提交信息创建独立提交。

---

## 阶段一：基础环境与规则

### 任务 1：建立项目规则和安全边界

**文件：**
- 创建：`AGENTS.md`
- 创建：`.gitignore`
- 创建：`.env.example`
- 修改：`README.md`
- 测试：`tests/smoke/test_repository_hygiene.py`

**接口：**
- 产出标准环境变量名、运行命令、目录约束和保密边界，供所有后续任务使用。

- [ ] 写失败测试：验证 `.env`、`.venv`、模型目录、上传文件目录、日志目录和构建目录被忽略，且 `.env.example` 不包含真实 Key。
- [ ] 运行：`python -m pytest tests/smoke/test_repository_hygiene.py -q`；预期失败，因为规则文件尚不存在。
- [ ] 写入 `AGENTS.md`，记录 Python 3.12、Node/npm、测试命令、目录职责、代码风格、禁止提交项和数据库变更规则。
- [ ] 写入 `.gitignore`，覆盖 `.env*`（保留 `.env.example`）、`.venv/`、`node_modules/`、模型权重、`backend/storage/`、日志、缓存、数据库和前端构建产物。
- [ ] 写入 `.env.example`，包含数据库、Redis、Milvus、DashScope、JWT、文件大小、配额、模型路径、检索 K 值和 CORS 配置。
- [ ] 写根 README，说明项目定位、首版/二阶段边界和后续启动入口。
- [ ] 运行测试，预期通过；检查 `git status --ignored` 确认真实 `.env` 不会被纳入提交。
- [ ] 提交：`git add AGENTS.md .gitignore .env.example README.md tests/smoke/test_repository_hygiene.py && git commit -m "chore: establish project rules and secret boundaries"`

### 任务 2：创建虚拟环境和应用脚手架

**文件：**
- 创建：`.python-version`
- 创建：`backend/requirements.txt`
- 创建：`backend/requirements-dev.txt`
- 创建：`backend/app/__init__.py`
- 创建：`backend/app/main.py`
- 创建：`backend/tests/test_health.py`
- 创建：`frontend/package.json`
- 创建：`frontend/vite.config.ts`
- 创建：`frontend/src/main.ts`

**接口：**
- `backend.app.main:create_app() -> FastAPI`
- `GET /api/v1/health/live -> {"status":"ok"}`

- [ ] 创建虚拟环境：`python -m venv .venv`，使用 `.venv/Scripts/python.exe`（Windows）或 `.venv/bin/python`（Unix）。
- [ ] 写失败测试：导入 `create_app` 并断言 live health 响应为 200。
- [ ] 运行：`backend/.venv...` 对应的 `pytest backend/tests/test_health.py -q`；预期失败，因为应用不存在。
- [ ] 创建 FastAPI 应用工厂、API 版本前缀和基础错误处理；添加 Vue/Vite 最小入口和 npm scripts。
- [ ] 安装开发依赖：`python -m pip install -r backend/requirements-dev.txt`；运行 `npm install --prefix frontend`。
- [ ] 运行后端测试、`npm run build --prefix frontend`，预期通过。
- [ ] 提交：`git add .python-version backend frontend && git commit -m "chore: scaffold backend and frontend applications"`

### 任务 3：配置层、日志和统一错误

**文件：**
- 创建：`backend/app/core/config.py`
- 创建：`backend/app/core/logging.py`
- 创建：`backend/app/core/errors.py`
- 创建：`backend/app/api/error_handlers.py`
- 测试：`backend/tests/core/test_config.py`
- 测试：`backend/tests/core/test_errors.py`

**接口：**
- `Settings.from_env() -> Settings`
- `AppError(code: str, message: str, status_code: int, details: dict | None)`
- `error_envelope(error: AppError, request_id: str) -> dict`

- [ ] 测试环境变量覆盖、默认值、缺少 API Key 的安全告警和敏感值不出现在日志。
- [ ] 运行：`pytest backend/tests/core/test_config.py backend/tests/core/test_errors.py -q`；预期初始失败。
- [ ] 实现 Pydantic Settings、结构化 logger、request ID middleware 和统一 JSON/SSE 错误码。
- [ ] 将 `Settings` 注入 FastAPI，不在模块导入时连接外部服务。
- [ ] 运行测试及 `python -m compileall backend/app`，预期通过。
- [ ] 提交：`git add backend/app/core backend/app/api/error_handlers.py backend/tests/core && git commit -m "feat: add configuration logging and error contracts"`

### 检查点 A：基础工程

- [ ] `.env.example` 无真实密钥，`.gitignore` 覆盖敏感和生成文件。
- [ ] 虚拟环境可创建，后端 health 测试通过，前端可以构建。
- [ ] 统一错误结构可用于 JSON 和 SSE。

## 阶段二：数据库、认证与会话

### 任务 4：SQLAlchemy 模型、迁移和数据库初始化

**文件：**
- 创建：`backend/app/db/session.py`
- 创建：`backend/app/db/base.py`
- 创建：`backend/app/models/user.py`
- 创建：`backend/app/models/chat_session.py`
- 创建：`backend/app/models/message.py`
- 创建：`backend/app/models/document.py`
- 创建：`backend/app/models/fqa.py`
- 创建：`backend/app/models/usage.py`
- 创建：`backend/app/models/feedback.py`
- 创建：`backend/migrations/env.py`
- 创建：`backend/migrations/versions/0001_initial_schema.py`
- 创建：`backend/scripts/init_db.py`
- 测试：`backend/tests/db/test_models.py`

**接口：**
- `get_session() -> Iterator[Session]`
- 模型表：`users`、`chat_sessions`、`messages`、`message_sources`、`message_feedback`、`documents`、`fqa_entries`、`usage_records`

- [ ] 写测试：SQLite 测试库创建全部表；邮箱/手机号唯一；消息、来源、文档和用户关系可持久化；usage 唯一键生效。
- [ ] 运行：`pytest backend/tests/db/test_models.py -q`；预期失败。
- [ ] 实现 UUID 主键、UTC 时间、软删除、文档状态、版本关联、索引和外键。
- [ ] 编写 Alembic 初始迁移，确保重复执行不会破坏已有数据库。
- [ ] 编写幂等 `init_db.py`，导入 FQA 和示例数据入口。
- [ ] 运行测试、`alembic upgrade head`（测试数据库）和 `alembic check`，预期通过。
- [ ] 提交：`git add backend/app/db backend/app/models backend/migrations backend/scripts/init_db.py backend/tests/db && git commit -m "feat: define database schema and migrations"`

### 任务 5：认证服务和鉴权依赖

**文件：**
- 创建：`backend/app/schemas/auth.py`
- 创建：`backend/app/services/auth_service.py`
- 创建：`backend/app/api/auth.py`
- 创建：`backend/app/core/security.py`
- 创建：`backend/tests/services/test_auth_service.py`
- 创建：`backend/tests/api/test_auth_api.py`

**接口：**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `class AuthService.register(identifier: str, password: str) -> User`
- `class AuthService.authenticate(identifier: str, password: str) -> TokenResponse`
- `get_current_user(...) -> User`

- [ ] 写失败测试：合法邮箱/手机号注册成功；重复标识返回 409；弱密码和非法标识返回 422；错误密码返回 401；JWT 过期/篡改返回 401。
- [ ] 运行两个测试文件，预期失败。
- [ ] 实现邮箱/中国大陆手机号识别、Argon2id、JWT access token、密码长度规则和安全错误消息。
- [ ] 注册和登录路由只依赖 Service；将 `get_current_user` 作为后续会话/文档/问答的统一依赖。
- [ ] 运行测试并检查响应不包含 `password_hash`。
- [ ] 提交：`git add backend/app/core/security.py backend/app/schemas/auth.py backend/app/services/auth_service.py backend/app/api/auth.py backend/tests && git commit -m "feat: add password authentication and JWT authorization"`

### 任务 6：会话、消息和反馈垂直切片

**文件：**
- 创建：`backend/app/schemas/session.py`
- 创建：`backend/app/schemas/message.py`
- 创建：`backend/app/services/session_service.py`
- 创建：`backend/app/api/sessions.py`
- 创建：`backend/app/api/messages.py`
- 测试：`backend/tests/api/test_sessions_api.py`

**接口：**
- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/messages`
- `PUT /api/v1/messages/{message_id}/feedback`

- [ ] 写测试：用户只能读写自己的会话和消息；删除为幂等软删除；反馈只能针对本用户会话中的 assistant 消息；重复反馈执行更新。
- [ ] 运行：`pytest backend/tests/api/test_sessions_api.py -q`；预期失败。
- [ ] 实现 Service、Repository 查询、鉴权归属、分页参数和反馈唯一约束。
- [ ] 将路由注册到 API 应用，返回稳定 Pydantic 响应。
- [ ] 运行测试及 OpenAPI schema 导出检查。
- [ ] 提交：`git add backend/app/schemas backend/app/services/session_service.py backend/app/api backend/tests/api/test_sessions_api.py && git commit -m "feat: add isolated chat sessions and feedback"`

### 检查点 B：数据与身份

- [ ] 迁移能在空数据库执行，模型测试通过。
- [ ] 邮箱/手机号注册登录和 JWT 鉴权通过。
- [ ] 会话、历史消息和反馈均执行用户隔离。

## 阶段三：FQA 与配额

### 任务 7：Redis 客户端、配额和 FQA 检索

**文件：**
- 创建：`backend/app/adapters/redis_client.py`
- 创建：`backend/app/services/usage_service.py`
- 创建：`backend/app/fqa/preprocess.py`
- 创建：`backend/app/fqa/bm25_search.py`
- 创建：`backend/app/services/fqa_service.py`
- 创建：`backend/scripts/seed_fqa.py`
- 测试：`backend/tests/fqa/test_bm25_search.py`
- 测试：`backend/tests/services/test_usage_service.py`

**接口：**
- `FQAService.query(question: str, user_id: str) -> FQAResult`
- `UsageService.reserve(user_id: UUID) -> UsageReservation`
- `UsageService.compensate(reservation: UsageReservation) -> None`

- [ ] 写测试：精确缓存优先；BM25 阈值命中返回标准答案；未命中返回 `should_use_rag=True`；第 101 次配额失败；失败流程补偿计数。
- [ ] 运行两个测试文件，预期失败。
- [ ] 实现 Redis 缓存、jieba 预处理、BM25、可配置阈值和 Redis/MySQL 双写配额。
- [ ] 设计 Redis 不可用时的受控降级，不绕过每日配额。
- [ ] 运行测试，使用 fake Redis，不连接外部服务。
- [ ] 提交：`git add backend/app/adapters/redis_client.py backend/app/fqa backend/app/services backend/scripts/seed_fqa.py backend/tests/fqa backend/tests/services/test_usage_service.py && git commit -m "feat: add FQA retrieval and daily usage limits"`

## 阶段四：文档存储与异步入库

### 任务 8：DocumentStorage 与文件上传 API

**文件：**
- 创建：`backend/app/adapters/document_storage.py`
- 创建：`backend/app/schemas/document.py`
- 创建：`backend/app/services/document_service.py`
- 创建：`backend/app/api/documents.py`
- 创建：`backend/tests/services/test_document_storage.py`
- 创建：`backend/tests/api/test_documents_upload.py`

**接口：**
- `DocumentStorage.save(stream, document_id, original_name) -> StoredFile`
- `DocumentStorage.delete(storage_path) -> None`
- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `DELETE /api/v1/documents/{document_id}`

- [ ] 写测试：允许 TXT/MD/PDF；拒绝其他扩展名、超大文件和空文件；SHA-256 稳定；文件和 pending 元数据创建；用户不能访问他人文档。
- [ ] 运行测试，预期失败。
- [ ] 实现安全文件名、用户目录隔离、大小限制、流式哈希、状态记录、列表和删除授权。
- [ ] 上传成功后只创建 pending 记录，暂不在 HTTP 请求内解析或向量化。
- [ ] 运行测试和路径穿越检查。
- [ ] 提交：`git add backend/app/adapters/document_storage.py backend/app/schemas/document.py backend/app/services/document_service.py backend/app/api/documents.py backend/tests && git commit -m "feat: add secure document upload and metadata APIs"`

### 任务 9：解析、清洗和父子块切分

**文件：**
- 创建：`backend/app/rag/parsers/base.py`
- 创建：`backend/app/rag/parsers/text_parser.py`
- 创建：`backend/app/rag/parsers/markdown_parser.py`
- 创建：`backend/app/rag/parsers/pdf_parser.py`
- 创建：`backend/app/rag/cleaner.py`
- 创建：`backend/app/rag/chunker.py`
- 测试：`backend/tests/rag/test_parsers.py`
- 测试：`backend/tests/rag/test_chunker.py`

**接口：**
- `DocumentParser.parse(path: Path) -> list[ParsedPage]`
- `clean_pages(pages: list[ParsedPage]) -> list[ParsedPage]`
- `ParentChildChunker.split(pages: list[ParsedPage]) -> list[ChunkRecord]`

- [ ] 写测试：TXT/MD/PDF 解析保留来源；扫描 PDF 返回明确 OCR 不支持错误；清洗保留标题/代码块；父块约 1000-1500 字符、子块约 250-400 字符且有 50-80 重叠；块元数据包含页码/章节/顺序。
- [ ] 运行两个测试文件，预期失败。
- [ ] 实现按扩展名选择解析器、PyMuPDF PDF 文本提取、Markdown 标题跟踪、空白清洗和父子块生成。
- [ ] 对超过单块大小的段落按稳定边界切分，避免生成空块。
- [ ] 运行测试并用三份示例材料手工检查块内容。
- [ ] 提交：`git add backend/app/rag/parsers backend/app/rag/cleaner.py backend/app/rag/chunker.py backend/tests/rag && git commit -m "feat: parse clean and split knowledge documents"`

### 任务 10：Embedding、Milvus Schema 和 Worker

**文件：**
- 创建：`backend/app/adapters/embedding.py`
- 创建：`backend/app/adapters/milvus_client.py`
- 创建：`backend/app/rag/indexer.py`
- 创建：`backend/app/workers/celery_app.py`
- 创建：`backend/app/workers/document_tasks.py`
- 创建：`backend/tests/rag/test_indexer.py`
- 创建：`backend/tests/workers/test_document_tasks.py`

**接口：**
- `EmbeddingProvider.embed(texts: list[str]) -> EmbeddingBatch`
- `MilvusClient.ensure_collection() -> None`
- `MilvusClient.insert(chunks: list[VectorChunk]) -> int`
- `MilvusClient.delete_by_document(document_id: UUID) -> None`
- `process_document(document_id: str) -> DocumentTaskResult`

- [ ] 写测试：Mock Embedding 生成 dense/sparse；Milvus schema 包含用户、文档版本、父子块、来源和 active_version；任务状态按 pending→processing→ready；失败清理已写向量并置 failed；外部临时异常重试。
- [ ] 运行测试，预期失败。
- [ ] 实现懒加载 bge-m3、设备自动选择、批量向量化、Milvus collection/index、用户和 active_version 过滤字段。
- [ ] 实现 Celery 任务：领取锁、解析、切分、向量化、写入、版本切换、失败回滚。
- [ ] 注册 Redis broker、worker 命令和任务路由；不在 API 进程启动时加载模型。
- [ ] 运行 Mock 测试；真实 Milvus 测试标记为 `integration`。
- [ ] 提交：`git add backend/app/adapters backend/app/rag/indexer.py backend/app/workers backend/tests && git commit -m "feat: add vector indexing worker and Milvus integration"`

### 检查点 C：知识库入库

- [ ] 上传 API 立即返回 202 和 pending 文档。
- [ ] TXT/MD/PDF 解析与父子块测试通过。
- [ ] Worker 使用 Mock 模型完成 ready/failed 状态流转。
- [ ] 删除路径同时覆盖文件、MySQL 和 Milvus 清理。

## 阶段五：RAG、Prompt 和 POST-SSE

### 任务 11：混合检索、RRF、父块回收和重排

**文件：**
- 创建：`backend/app/rag/retrieval/contracts.py`
- 创建：`backend/app/rag/retrieval/hybrid_direct.py`
- 创建：`backend/app/rag/retrieval/rrf.py`
- 创建：`backend/app/rag/retrieval/parent_recovery.py`
- 创建：`backend/app/adapters/reranker.py`
- 创建：`backend/tests/rag/test_retrieval.py`

**接口：**
- `RetrievalStrategy.retrieve(question: str, user_id: UUID, source_filter: list[str] | None) -> RetrievalResult`
- `rrf_fuse(dense: list[SearchHit], sparse: list[SearchHit], k: int) -> list[SearchHit]`
- `recover_parents(hits: list[SearchHit]) -> list[ContextDocument]`
- `Reranker.rank(question: str, contexts: list[ContextDocument]) -> list[ContextDocument]`

- [ ] 写测试：Dense/Sparse 结果规范化；RRF 共同命中排名更高；子块按 parent_id 聚合；source_filter 在所有查询路径生效；reranker Mock 排序；不可用时退化并输出 warning；active_version 和 user_id 必须过滤。
- [ ] 运行测试，预期失败。
- [ ] 实现 `HybridDirectStrategy`，保留 HyDE/SubQuery/Backtracking 接口但不调用。
- [ ] 实现候选 K、最终 Top-N、相似度阈值和章节/版本排序配置。
- [ ] 运行单元测试和静态类型检查。
- [ ] 提交：`git add backend/app/rag/retrieval backend/app/adapters/reranker.py backend/tests/rag/test_retrieval.py && git commit -m "feat: implement hybrid retrieval with fusion and reranking"`

### 任务 12：Prompt、证据兜底和 LLM Provider

**文件：**
- 创建：`backend/app/rag/prompts.py`
- 创建：`backend/app/rag/context_builder.py`
- 创建：`backend/app/adapters/llm_provider.py`
- 创建：`backend/app/adapters/dashscope_provider.py`
- 创建：`backend/app/services/qa_service.py`
- 测试：`backend/tests/rag/test_prompts.py`
- 测试：`backend/tests/services/test_qa_service.py`

**接口：**
- `build_context(contexts: list[ContextDocument], token_budget: int) -> str`
- `build_rag_messages(question: str, history: list[Message], context: str) -> list[ChatMessage]`
- `LLMProvider.complete(messages: list[ChatMessage]) -> str`
- `LLMProvider.stream(messages: list[ChatMessage]) -> AsyncIterator[str]`
- `QAService.answer(question, session_id, user_id) -> QAResult`

- [ ] 写测试：Prompt 包含系统约束、最近 N 轮历史、来源 ID/文档/页码/章节；上下文超预算先截断历史；无证据返回 fallback；文档内 Prompt 注入不会改变系统规则；Mock LLM 输出稳定。
- [ ] 运行两个测试文件，预期失败。
- [ ] 实现严格 evidence-only Prompt、版本冲突提示、来源标记和上下文预算。
- [ ] 实现 DashScope OpenAI 兼容 Provider、超时/有限重试和 Mock Provider；不把 Key 写入日志。
- [ ] 将 FQA 结果和 RAG 结果统一为 QAResult，记录 answer_type、retrieval_strategy、sources 和 latency。
- [ ] 运行测试、类型检查和 Prompt 快照检查。
- [ ] 提交：`git add backend/app/rag/prompts.py backend/app/rag/context_builder.py backend/app/adapters/llm_provider.py backend/app/adapters/dashscope_provider.py backend/app/services/qa_service.py backend/tests && git commit -m "feat: add grounded prompts and LLM provider boundary"`

### 任务 13：POST-SSE 流式问答 API

**文件：**
- 创建：`backend/app/schemas/query.py`
- 创建：`backend/app/api/query.py`
- 创建：`backend/app/api/sse.py`
- 修改：`backend/app/main.py`
- 测试：`backend/tests/api/test_query_api.py`
- 测试：`backend/tests/api/test_sse_contract.py`

**接口：**
- `POST /api/v1/query`：JSON 非流式回答。
- `POST /api/v1/query/stream`：`text/event-stream`。
- `serialize_event(event_type: str, payload: dict) -> str`

- [ ] 写测试：未授权、超长问题、无效 session、配额超限、FQA 命中、RAG Mock 输出和错误均返回稳定 JSON/SSE；事件顺序为 start→delta/source*→done 或 error。
- [ ] 运行两个测试文件，预期失败。
- [ ] 实现 POST body、Bearer 鉴权、配额预占/补偿、QAService 调用和流式消息持久化。
- [ ] Provider 每个 chunk 立即序列化为 delta；来源在 done 前发送；禁止对完整字符串逐字符迭代。
- [ ] 客户端断开时取消可取消任务；失败消息标记 failed，完成消息保存来源。
- [ ] 运行测试并用 httpx 读取完整 SSE 流验证事件协议。
- [ ] 提交：`git add backend/app/schemas/query.py backend/app/api/query.py backend/app/api/sse.py backend/app/main.py backend/tests/api && git commit -m "feat: add grounded POST SSE question answering"`

### 检查点 D：后端核心闭环

- [ ] FQA 命中无需调用 LLM，未命中走 Hybrid RAG。
- [ ] RAG 具备 Dense/Sparse、RRF、父块、重排、Prompt、来源和 fallback。
- [ ] POST-SSE 是真实 Provider 流，不是逐字符模拟。
- [ ] 消息、来源、反馈和配额均持久化/隔离。

## 阶段六：前端核心体验

### 任务 14：Vue 路由、状态和 API 客户端

**文件：**
- 创建：`frontend/src/router/index.ts`
- 创建：`frontend/src/stores/auth.ts`
- 创建：`frontend/src/stores/chat.ts`
- 创建：`frontend/src/stores/documents.ts`
- 创建：`frontend/src/api/http.ts`
- 创建：`frontend/src/api/queryStream.ts`
- 测试：`frontend/tests/api/queryStream.test.ts`

**接口：**
- `parseSSEStream(response: Response, onEvent: (event: SSEEvent) => void) -> Promise<void>`
- `authStore.login/register/logout`
- `chatStore.createSession/loadMessages/streamQuestion`
- `documentsStore.upload/list/remove`

- [ ] 写测试：自动附加 Bearer；SSE 正确解析多行 data、start/delta/source/done/error；断线进入可重试状态；token 失效清空登录态。
- [ ] 运行：`npm test --prefix frontend -- --run frontend/tests/api/queryStream.test.ts`；预期失败。
- [ ] 实现 API client、Pinia stores、路由守卫、fetch-based SSE parser 和统一错误映射。
- [ ] 运行 Vitest 和 `npm run build --prefix frontend`。
- [ ] 提交：`git add frontend/src frontend/tests && git commit -m "feat: add frontend API clients and application state"`

### 任务 15：认证、会话聊天和来源引用界面

**文件：**
- 创建：`frontend/src/views/LoginView.vue`
- 创建：`frontend/src/views/RegisterView.vue`
- 创建：`frontend/src/views/ChatView.vue`
- 创建：`frontend/src/components/SessionSidebar.vue`
- 创建：`frontend/src/components/MessageList.vue`
- 创建：`frontend/src/components/SourceCitations.vue`
- 创建：`frontend/src/components/FeedbackButtons.vue`
- 创建：`frontend/src/styles/theme.css`
- 测试：`frontend/tests/chat/ChatView.test.ts`

**接口：**
- 登录/注册表单提交 `identifier/password`。
- ChatView 通过 `chatStore.streamQuestion` 渲染事件。

- [ ] 写测试：注册/登录表单校验；创建/切换/删除会话；delta 增量渲染；source 展开；done 后刷新历史；error 可重试；赞/踩调用反馈接口。
- [ ] 运行测试，预期失败。
- [ ] 实现响应式工作台、空状态、加载状态、断线状态、配额错误和键盘可访问控件。
- [ ] 使用 Markdown 渲染时对 HTML 进行安全处理；不在浏览器暴露 LLM 配置。
- [ ] 运行 Vitest、构建并检查移动端布局。
- [ ] 提交：`git add frontend/src/views frontend/src/components frontend/src/styles frontend/tests/chat && git commit -m "feat: build authenticated streaming chat experience"`

### 任务 16：知识库管理界面

**文件：**
- 创建：`frontend/src/views/DocumentsView.vue`
- 创建：`frontend/src/components/DocumentUploader.vue`
- 创建：`frontend/src/components/DocumentStatus.vue`
- 测试：`frontend/tests/documents/DocumentsView.test.ts`

**接口：**
- 上传 multipart 到 `POST /api/v1/documents`。
- 列表轮询 `GET /api/v1/documents`，删除调用 `DELETE /api/v1/documents/{id}`。

- [ ] 写测试：限制 TXT/MD/PDF、显示 pending/processing/ready/failed、展示失败原因、删除确认和刷新列表。
- [ ] 运行测试，预期失败。
- [ ] 实现拖放/选择上传、进度和状态轮询；删除后从列表移除并显示失败重试。
- [ ] 运行测试、构建和手动检查窄屏布局。
- [ ] 提交：`git add frontend/src/views/DocumentsView.vue frontend/src/components/DocumentUploader.vue frontend/src/components/DocumentStatus.vue frontend/tests/documents && git commit -m "feat: add knowledge document management UI"`

### 检查点 E：前后端功能联通

- [ ] 前端可以注册、登录、创建会话、查看历史。
- [ ] 前端可以上传文档并显示异步状态。
- [ ] 前端可以解析 SSE 并展示答案、来源、反馈和错误。

## 阶段七：Docker、集成测试与文档

### 任务 17：Docker Compose 双模式和初始化数据

**文件：**
- 创建：`docker-compose.yml`
- 创建：`docker/mysql/init.sql`
- 创建：`backend/Dockerfile`
- 创建：`frontend/Dockerfile`
- 修改：`.env.example`
- 测试：`backend/tests/integration/test_compose_config.py`

**接口：**
- 默认 profile：MySQL、Redis、Milvus、etcd、MinIO。
- `app` profile：backend、worker、frontend。

- [ ] 写测试：Compose YAML 包含健康检查、命名卷、网络、基础设施服务和 app profile；端口与 `.env.example` 一致。
- [ ] 运行：`docker compose config`；预期初始失败。
- [ ] 实现双模式 Compose、MySQL 初始化、backend/worker/frontend 镜像、模型目录挂载和文档卷。
- [ ] 使用非 root 应用用户；模型不复制进镜像；启动命令显式执行迁移。
- [ ] 运行 `docker compose config`，若 Docker 可用则执行 `docker compose up -d mysql redis etcd minio milvus` 和健康检查。
- [ ] 提交：`git add docker-compose.yml docker backend/Dockerfile frontend/Dockerfile .env.example backend/tests/integration && git commit -m "feat: add dual-mode Docker deployment"`

### 任务 18：集成、浏览器和 RAG 评测

**文件：**
- 创建：`backend/tests/integration/test_mysql_migrations.py`
- 创建：`backend/tests/integration/test_milvus_lifecycle.py`
- 创建：`backend/tests/e2e/test_core_flow.py`
- 创建：`frontend/playwright.config.ts`
- 创建：`frontend/tests/e2e/core-flow.spec.ts`
- 创建：`sample-data/product-faq.md`
- 创建：`sample-data/refund-policy.txt`
- 创建：`sample-data/account-guide.txt`
- 创建：`backend/evaluation/dataset.json`
- 创建：`backend/evaluation/evaluate.py`

**接口：**
- `pytest -m integration`
- `npx playwright test`
- `python backend/evaluation/evaluate.py`

- [ ] 写集成用例：迁移、文档入库/删除、过滤检索、用户隔离和 Mock LLM 完整问答。
- [ ] 写浏览器用例：注册→登录→上传→ready→提问→SSE→来源→反馈→删除→不可检索。
- [ ] 写评测集和脚本，记录检索命中率、来源正确性、fallback 正确性和延迟；无真实 API Key 时使用 Mock。
- [ ] 运行单元测试、集成测试（环境可用时）和 Playwright；记录每项命令输出。
- [ ] 提交：`git add backend/tests frontend/tests sample-data backend/evaluation && git commit -m "test: add integration browser and RAG evaluation coverage"`

### 任务 19：完成项目文档和 AI 使用说明

**文件：**
- 创建：`docs/project-overview.md`
- 创建：`docs/api.md`
- 创建：`docs/database.md`
- 创建：`docs/ai-architecture.md`
- 创建：`docs/business-flow.md`
- 创建：`docs/deployment.md`
- 创建：`docs/testing.md`
- 创建：`docs/ai-usage.md`
- 创建：`docs/agent-challenge.md`
- 修改：`README.md`
- 修改：`backend/README.md`
- 修改：`frontend/README.md`

**接口：**
- 文档中的启动命令、API 路径、字段、SSE 事件和目录必须与实现一致。

- [ ] 对照原始笔试文档逐项写技术选型、RAG 图、Prompt、Top-K/阈值理由、幻觉控制、长文档防遗漏、验证方式和 AI 工具人工审查。
- [ ] API 文档给出注册、登录、上传、问答、流式、历史、反馈、删除请求/响应和错误示例。
- [ ] 数据库文档包含 ER Mermaid 图、字段、索引、版本和删除生命周期。
- [ ] 部署文档包含创建虚拟环境、安装依赖、`.env`、Docker、迁移、示例数据、启动、测试和模型目录。
- [ ] Agent 挑战题只写设计、依赖图和执行顺序，明确不属于首版实现。
- [ ] 运行链接检查、命令校验和文档中的 smoke 命令。
- [ ] 提交：`git add docs README.md backend/README.md frontend/README.md && git commit -m "docs: complete project API architecture and deployment guides"`

### 检查点 F：交付前验证

- [ ] `pytest` 单元测试全部通过。
- [ ] `npm test`、`npm run build` 全部通过。
- [ ] Docker Compose 配置和基础设施健康检查通过。
- [ ] 核心浏览器流程通过，或明确记录外部依赖阻塞及替代 Mock 验证。
- [ ] RAG 评测报告生成，未提交任何真实密钥或模型权重。

## 阶段八：GitHub 交付

### 任务 20：安全扫描、干净克隆和 GitHub 推送

**文件：**
- 修改：`.gitignore`（如扫描发现遗漏）
- 修改：`README.md`（如干净克隆步骤不完整）

**接口：**
- 远程仓库：`wangzhi0510-spec/ai-Smart-Customer-Service`
- 默认分支：`main`

- [ ] 运行 `git status --short`、`git diff --check`、`git log --oneline`。
- [ ] 扫描提交内容：`git grep -n -i -E "api[_-]?key|password|secret|token" -- ':!*.example'`，确认没有真实凭据。
- [ ] 在临时目录执行干净 clone，按部署文档完成配置检查、前端构建和后端 smoke；需要真实模型/服务的步骤使用明确的 integration 标记。
- [ ] 配置 `origin` 为用户提供的仓库，确认默认分支和远程状态。
- [ ] 通过已连接 GitHub 工具创建/更新远程文件或提交，并推送已验证提交；不上传 `.env`、模型、数据库和构建产物。
- [ ] 使用 GitHub 工具读取远程提交/文件，确认 README、设计文档和代码可见。
- [ ] 提交最终修正：`git add -A && git commit -m "chore: prepare first release for GitHub"`。

## 最终验收清单

- [ ] 需求文档强制功能逐项对应实现和测试。
- [ ] 首版 RAG 为真实 Dense + Sparse + RRF + 父块 + 重排 + Prompt + LLM + SSE。
- [ ] FQA 命中、未命中、无证据兜底和每日配额可验证。
- [ ] 文档上传、异步状态、版本更新和删除后三层清理可验证。
- [ ] 用户、会话、消息、来源、反馈和文档严格隔离。
- [ ] Docker 基础设施模式和完整 app profile 均可解析；模型通过挂载提供。
- [ ] 前端核心闭环可在浏览器完成。
- [ ] 中文文档完整，包含 AI 使用说明和 Agent 挑战设计。
- [ ] 全量测试、密钥扫描、干净 clone smoke 和 GitHub 远程核验完成。

