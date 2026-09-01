# AI 智能客服系统任务清单

规格：`docs/superpowers/specs/2026-08-28-AI智能客服系统设计文档.md`

详细计划：`docs/superpowers/plans/2026-08-28-ai-smart-customer-service-implementation-plan.md`

## 阶段一：基础环境与规则

- [x] 任务 1：建立项目规则、`.gitignore`、`.env.example` 和仓库安全测试。
- [x] 任务 2：创建 Python 虚拟环境、FastAPI/Vue 脚手架和 health 测试。
- [x] 任务 3：实现配置层、结构化日志、request ID 和统一错误协议。

### 检查点 A

- [x] 密钥和生成文件忽略规则通过测试。
- [x] 后端 health 测试通过，前端构建通过。

## 阶段二：数据库、认证与会话

- [x] 任务 4：创建 SQLAlchemy 模型、Alembic 初始迁移和初始化脚本。
- [x] 任务 5：实现邮箱/手机号注册登录、Argon2id 和 JWT 鉴权。
- [x] 任务 6：实现会话、历史消息、软删除和赞/踩反馈。

### 检查点 B

- [x] 数据库迁移、认证和用户隔离测试通过。

## 阶段三：FQA 与配额

- [x] 任务 7：实现 Redis 缓存、每日 100 次配额、精确 FQA 和 BM25 检索。

## 阶段四：文档存储与异步入库

- [x] 任务 8：实现安全文件存储、TXT/MD/PDF 上传、元数据和删除 API。
- [x] 任务 9：实现文档解析、清洗和父子块切分。
- [x] 任务 10：实现 bge-m3、Milvus Schema、Celery Worker 和版本化入库。

### 检查点 C

- [x] 上传后异步状态、入库成功/失败、更新和三层删除可验证。

## 阶段五：RAG、Prompt 和 POST-SSE

- [x] 任务 11：实现 Dense/Sparse 检索、RRF、父块回收和重排降级。
- [x] 任务 12：实现证据型 Prompt、长文档策略、DashScope Provider 和 FQA/RAG 编排。
- [x] 任务 13：实现非流式问答和真实 POST-SSE `start/delta/source/done/error`。

### 检查点 D

- [x] FQA + 完整 RAG + 来源引用 + fallback + 真流式后端闭环通过。

## 阶段六：前端核心体验

- [x] 任务 14：实现 Vue 路由、Pinia 状态、API 客户端和 SSE 解析器。
- [x] 任务 15：实现认证、会话聊天、来源、反馈和响应式界面。
- [x] 任务 16：实现知识库上传、状态、失败原因和删除界面。

### 检查点 E

- [x] 浏览器可完成登录、上传、流式问答、来源、反馈和删除。

## 阶段七：Docker、测试与文档

- [x] 任务 17：实现 Docker Compose 基础设施模式和完整 app profile。
- [x] 任务 18：实现集成测试、Playwright 核心流程和 RAG 评测集。
- [x] 任务 19：完成项目、API、数据库、AI 架构、业务、部署、测试、AI 使用和 Agent 挑战文档。

### 检查点 F

- [x] 单元、前端、集成、浏览器、Docker 和 RAG 评测验证完成。

## 阶段八：GitHub 交付

- [x] 任务 20：密钥扫描、GitHub 工具上传和远程核验；干净 clone 因 GitHub HTTPS 连接重置未完成。

## 最终验收

- [x] 原始笔试文档所有强制项均有实现、测试或交付文档对应项。
- [x] 首版核心闭环在本地隔离测试环境中可按 README 启动并验证；独立 clone 受 GitHub 网络重置阻塞。
- [ ] GitHub `main` 不包含密钥、模型、虚拟环境、上传文件或构建产物。

## 阶段九：本地 Docker 运行闭环修复

- [x] 任务 21：修复 Celery 文档任务注册并验证 Worker 消费。
- [x] 任务 22：初始化 Milvus Dense/Sparse 索引并验证真实检索。

## 阶段十：示例知识库与启动自动向量化

- [x] 任务 23：完成示例知识文档和演示账号初始化设计。
- [ ] 任务 24：实现 Docker seed 幂等导入、自动向量化和端到端验证。

## 阶段十一：删除后检索一致性修复

- [x] 任务 25：修复删除文档后的 Milvus 残留并验证来源不再出现。

## 阶段十二：聊天布局滚动隔离

- [x] 任务 26：修复桌面端会话栏与聊天内容联动滚动，并验证响应式布局。

## 阶段十三：会话自动创建与标题编辑

- [ ] 任务 27：无会话时自动创建默认会话，并支持用户重命名会话。
