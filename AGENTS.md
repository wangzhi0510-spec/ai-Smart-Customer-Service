# AI 智能客服系统协作规则

## 需求优先级

- 《AI开发工程师笔试题.docx》是需求、设计和验收的第一标准。
- 已批准设计位于 `docs/superpowers/specs/2026-08-28-AI智能客服系统设计文档.md`。
- 已批准计划位于 `docs/superpowers/plans/2026-08-28-ai-smart-customer-service-implementation-plan.md`。
- 首版只实现核心闭环；第二阶段功能只能预留真实接口，不得用空接口伪装完成。

## 技术基线

- Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic。
- Vue 3、TypeScript、Vite、Pinia，使用 npm。
- MySQL、Redis、Milvus、etcd、MinIO 通过 Docker Compose 提供。
- 默认 LLM 为 DashScope `qwen-plus`，Embedding 为本地 `bge-m3`，重排为本地 `bge-reranker-large`。

## 开发顺序

1. 每个任务先更新 `tasks/todo.md` 的状态。
2. 新功能和缺陷修复必须先写失败测试并确认失败原因正确。
3. 只写让当前测试通过的最小实现，再进行不改变行为的整理。
4. 先运行定向测试，再运行相关测试和阶段检查。
5. 验证通过后检查差异与敏感信息，创建单一职责提交。
6. 每个已验证提交及时同步到 GitHub，并从远程回读核验。
7. 当前任务未通过，不得开始下一个任务。

## 代码约定

- 后端采用 API、Service、Repository、Adapter、RAG 分层；路由不得直接访问数据库或外部模型。
- 外部服务通过接口注入，单元测试使用确定性 Fake 或 Mock。
- Pydantic Schema 与 SQLAlchemy Model 分离。
- 所有业务主键使用 UUID，时间以 UTC 保存。
- 所有用户资源必须校验当前 Token 用户归属。
- 所有错误使用稳定错误码；不得向客户端暴露堆栈、密钥或内部连接信息。
- 前端不得保存或调用 LLM API Key；流式问答使用 POST + fetch 读取 SSE。

## 测试命令

- 后端定向测试：`python -m pytest <test-path> -q`
- 后端全量测试：`python -m pytest -q`
- 前端测试：`npm test --prefix frontend -- --run`
- 前端构建：`npm run build --prefix frontend`
- Docker 配置：`docker compose config`
- 差异检查：`git diff --check`

## 安全边界

- 禁止提交 `.env`、真实 API Key、JWT 密钥、数据库密码、用户上传文件、模型权重、数据库文件、日志和构建产物。
- `.env.example` 中所有秘密字段必须为空；示例用户名和非秘密默认值可以保留。
- 日志不得包含密码、Token、Prompt、文档正文或 API Key。
- 文件上传必须校验类型、大小、空文件和路径穿越。
- 任何数据库结构变化都必须通过 Alembic 迁移并配套测试。

## Git 约定

- 使用短期分支，提交信息遵循 `feat/fix/test/docs/chore/refactor` 格式。
- 每个提交只完成一个可验证目标，不混入无关格式化或重构。
- 提交前运行任务要求的测试、`git diff --check` 和敏感信息检查。
- 不得强推共享分支，不得使用破坏性 reset 清除用户修改。

