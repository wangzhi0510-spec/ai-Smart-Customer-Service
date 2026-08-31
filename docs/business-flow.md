# 业务流程

## 1. 注册与登录

```mermaid
sequenceDiagram
  participant U as 用户
  participant F as Vue 前端
  participant A as Auth API
  participant S as AuthService
  participant DB as MySQL
  U->>F: 提交邮箱/手机号和密码
  F->>A: POST /api/v1/auth/register 或 /login
  A->>S: 校验 identifier、哈希/验证密码
  S->>DB: 创建或读取 users
  S-->>A: 用户与 JWT
  A-->>F: access_token + user
  F->>F: 保存 token，进入聊天工作台
```

密码只保存 Argon2id 哈希。后端从 Token subject 获取用户 UUID，不信任客户端提交的 `user_id`。

## 2. 文档上传与异步入库

```mermaid
sequenceDiagram
  participant U as 用户
  participant A as Documents API
  participant DS as DocumentService
  participant FS as DocumentStorage
  participant DB as MySQL
  participant Q as Redis/Celery
  participant W as Document Worker
  participant M as Milvus
  U->>A: multipart 上传 TXT/MD/PDF
  A->>DS: 校验归属、类型、大小、非空
  DS->>FS: 流式保存并计算 SHA-256
  DS->>DB: 创建 pending 文档
  DS->>Q: 投递 document_id
  A-->>U: 202 + 文档元数据
  Q->>W: 领取任务
  W->>DB: pending → processing
  W->>FS: 解析、清洗、切块
  W->>M: 写入新版本向量
  W->>DB: processing → ready，停用旧版本
  W-->>DB: 失败时 failed + error_code
```

处理状态：`pending`、`processing`、`ready`、`failed`。失败只重试外部临时故障；空文件、格式错误和不支持 OCR 的扫描 PDF 直接失败。删除必须清理向量、原文件和数据库元数据，操作幂等。

## 3. 问答闭环

```mermaid
flowchart TD
  Q[提交问题] --> Auth[校验 Token 与 session 归属]
  Auth --> Len[校验 1-500 字符]
  Len --> Quota[Redis 原子预占每日配额]
  Quota --> FQA{FQA 命中?}
  FQA -->|是| FAnswer[直接返回 FQA 答案]
  FQA -->|否| Hybrid[Dense + Sparse 检索]
  Hybrid --> RRF[RRF 融合]
  RRF --> Parent[父块回收]
  Parent --> Rank[重排或顺序降级]
  Rank --> Evidence{有充分证据?}
  Evidence -->|否| Fallback[标准知识库兜底]
  Evidence -->|是| Prompt[系统规则 + 历史 + 上下文]
  Prompt --> LLM[DashScope 流式生成]
  FAnswer --> Persist[持久化消息]
  Fallback --> Persist
  LLM --> Sources[发送来源事件]
  Sources --> Persist
  Persist --> Feedback[可选赞/踩反馈]
```

合法问题计入每日配额；参数校验失败、基础设施失败或 Provider 失败会补偿预占。问候语和精确 FQA 不调用 LLM。

## 4. SSE 事件时序

客户端使用 `fetch` 发起 POST 请求并读取 `text/event-stream`：

```text
event: start   -> request_id, message_id
event: delta   -> text（可多次）
event: source  -> document_id, document_name, page_number, excerpt
event: done    -> message_id, answer_type, retrieval_strategy, latency_ms
```

发生受控异常时返回 `event: error`，事件中只包含稳定错误码、安全提示和 request_id。Provider 产生的片段会立即转发，不能把完整答案拆成伪流式字符。

## 5. 删除后的可见性

删除文档后，文档列表不再返回可用记录；Milvus 中按 `document_id` 清理实体；检索额外过滤 `user_id`、`active_version` 和 `source_filter`。因此删除后的相同问题只能进入 fallback，不会继续引用旧版本。