# 示例知识库与启动自动向量化设计

日期：2026-08-31
状态：待用户审核

## 1. 背景与目标

为便于首版 AI 智能客服系统启动后立即进行检索和问答测试，增加一组受版本控制的示例知识文档，并在本地 Docker 启动期间自动完成演示账号创建、文档元数据写入、异步解析切分和 Milvus 向量化。

目标：

- 提供 `公司产品介绍.txt`、`常见问题FAQ.md`、`退换货政策.txt` 三个示例文档；
- 三个文档合计约 2000–5000 个汉字，覆盖产品、账户、订单、支付、物流、退款和换货场景；
- 首次启动后示例文档状态最终为 `ready`，可用于真实 RAG 问答和来源引用；
- 重复启动或重复执行初始化不会重复创建用户、文档或向量；
- 所有用户资源继续遵守当前 Token 用户归属校验。

## 2. 方案选择

采用独立的一次性 Docker `seed` 服务，而不是在 FastAPI 进程启动钩子中同步执行：

- 不阻塞 Backend 对健康检查和 API 请求的响应；
- 初始化失败可单独重试，不影响 API 和 Worker 长期运行；
- 复用现有 DocumentTaskProcessor/Celery/Milvus 真实链路；
- 方便后续替换为生产环境的知识库导入任务。

## 3. 组件与数据流

```text
Docker Compose 启动
    -> seed 等待 backend、mysql、redis、milvus、worker
    -> 幂等创建演示用户
    -> 读取 examples/knowledge_base/*.txt|*.md
    -> 计算 SHA-256 并检查 documents 元数据
    -> 新文件写入文档存储和 MySQL，投递 Celery 任务
    -> Worker 解析、清洗、父子块切分、Embedding、Milvus insert/activate
    -> seed 轮询文档状态直到 ready 或报告稳定失败
```

## 4. 演示账号

- 用户名由 `DEMO_USER_IDENTIFIER` 配置，默认值可使用非秘密示例邮箱；
- 密码只从 `DEMO_USER_PASSWORD` 读取；
- `.env.example` 中密码字段必须为空；
- 初始化脚本使用现有密码哈希逻辑创建或复用用户；
- 不在日志中输出密码、Token、Prompt 或文档正文。

演示文档归属于演示账号，用户登录后可在聊天页检索。普通用户仍只能检索自己拥有的文档。

## 5. 幂等规则

以演示用户、原始文件名和内容 SHA-256 作为幂等判断依据：

- 已存在相同用户、文件名、SHA-256 且状态为 `ready`：跳过复制、数据库写入和任务投递；
- 已存在相同内容但处于 `pending`/`processing`：只等待现有任务完成；
- 内容 SHA-256 变化：创建新版本文档并重新入库，不覆盖历史记录；
- 初始化失败：保留 `failed` 状态和稳定错误码，seed 进程返回失败，便于重试。

## 6. Docker 变更

新增 `seed` 服务：

- 使用现有 Backend 镜像和只读示例文档挂载；
- 使用同一数据库、Redis、Milvus、文档存储卷和模型挂载；
- 通过 `depends_on` 等待基础设施和 Backend 健康；
- 命令执行 `python -m backend.scripts.seed_demo_knowledge`；
- 不暴露端口，不常驻运行；
- 保留 `app` profile，默认启动命令仍可启动全套服务。

## 7. 测试与验收

后端：

- 示例文档文件存在、扩展名受支持、总字数在 2000–5000 范围；
- 首次初始化创建演示用户和三个文档，并投递任务；
- 第二次初始化不重复创建文档或任务；
- Worker 完成后文档为 `ready`，Milvus 向量可检索且版本激活；
- 失败时返回稳定错误码，不泄露内部异常。

Docker/端到端：

- `docker compose config --quiet` 通过；
- 本地 Compose 启动后 seed 成功退出；
- 使用演示账号登录后，针对三个主题提问均能返回 RAG 答案和来源；
- 普通用户不能读取演示账号的文档。

## 8. 非目标

- 不实现生产环境多租户共享知识库；
- 不把真实 API Key、密码、模型权重或运行时上传文件提交到 Git；
- 不把第二阶段的 HyDE、SubQuery、Backtracking 等检索策略提前实现。
