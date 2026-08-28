# AI 智能客服系统

基于 Vue 3、FastAPI、MySQL、Redis、Milvus 和大语言模型的企业智能客服系统。项目以《AI开发工程师笔试题.docx》为第一需求标准，首版实现用户认证、会话管理、知识库管理、FQA 高频问答、混合检索 RAG、真实 SSE 流式回答、来源引用和完整测试交付。

## 当前阶段

项目正在严格按照批准的设计和实施计划逐任务开发。当前仓库首先建立开发规则、环境安全边界和可验证的工程基础，业务代码将在前置门禁通过后逐步加入。

## 首版核心闭环

```text
用户注册/登录
  → 创建独立会话
  → 上传 TXT/Markdown/PDF
  → Worker 解析、切分、bge-m3 向量化并写入 Milvus
  → FQA 高频问答优先
  → Dense + Sparse 混合检索
  → RRF 融合、父块回收、重排
  → DashScope qwen-plus 生成
  → POST-SSE 实时输出答案和来源
  → 保存历史并提交赞/踩反馈
```

## 已批准文档

- [系统设计规格](docs/superpowers/specs/2026-08-28-AI智能客服系统设计文档.md)
- [详细实施计划](docs/superpowers/plans/2026-08-28-ai-smart-customer-service-implementation-plan.md)
- [任务清单](tasks/todo.md)

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia
- 后端：Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic
- 基础设施：MySQL 8、Redis 7、Milvus、etcd、MinIO、Docker Compose
- AI：bge-m3、bge-reranker-large、DashScope qwen-plus
- 测试：pytest、Vitest、Playwright

## 安全说明

复制 `.env.example` 为 `.env` 后填写本地配置。真实 `.env`、API Key、JWT 密钥、数据库密码、模型权重和用户上传文件不会提交到 Git。

完整安装、启动、测试和部署命令将在对应功能完成并通过验证后加入，避免文档声明尚不可运行的步骤。
