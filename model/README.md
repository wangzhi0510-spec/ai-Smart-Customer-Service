# 本地模型目录

此目录用于本地 Docker 运行时挂载模型权重，目录结构必须为：

```text
model/
├── embedding/bge-m3/
├── reranker/bge-reranker-large/
└── classifier/                 # 可选，意图分类扩展
```

当前开发机模型来源：

```text
D:\code\python_ai\code_edu_agent\backend\models
```

已将该目录复制到本地 `model/`。权重文件（`.bin`、`.safetensors`、`.pt` 等）约 4.7GB，受 `.gitignore` 忽略，不上传 GitHub，也不复制进 Docker 镜像。部署到新机器时请从受信任的模型仓库下载同名模型，或通过 `MODEL_HOST_PATH` 指向已有模型目录。

Docker Compose 会把 `${MODEL_HOST_PATH:-./model}` 只读挂载到容器 `/models`，后端使用：

```text
/models/embedding/bge-m3
/models/reranker/bge-reranker-large
```
