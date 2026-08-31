# API 文档

基础前缀：`/api/v1`。除健康检查外均需 `Authorization: Bearer <access_token>`。

## 统一错误

```json
{"error":{"code":"VALIDATION_ERROR","message":"请求参数无效","details":{},"request_id":"uuid"}}
```

常见错误码：`VALIDATION_ERROR`、`UNAUTHORIZED`、`NOT_FOUND`、`QUOTA_EXCEEDED`、`UNSUPPORTED_FILE_TYPE`、`DUPLICATE_DOCUMENT`、`QA_UNAVAILABLE`、`QA_FAILED`。

## 认证

- `POST /auth/register`：JSON `{ "identifier": "user@example.com", "password": "至少 8 位密码" }`，成功 `201`，返回 `access_token`、`token_type` 和 `user`。
- `POST /auth/login`：请求字段同注册，成功 `200`，响应结构同上。
- `GET /auth/me`：返回 `{id,email,phone,status}`。

## 会话和消息

- `POST /sessions`：`{"title":"售后咨询"}`，成功 `201`。
- `GET /sessions?page=1&page_size=20`：当前用户未删除会话列表。
- `GET /sessions/{session_id}`：会话详情，越权返回 `404`。
- `DELETE /sessions/{session_id}`：软删除，`204 No Content`。
- `GET /sessions/{session_id}/messages`：按创建时间返回消息及来源。
- `PUT /messages/{message_id}/feedback`：`{"rating":"positive","comment":"有帮助"}`；同一用户重复提交会更新。

## 文档

- `POST /documents`：`multipart/form-data` 字段 `file`，支持 `.txt`、`.md`、`.pdf`，默认 20 MiB，成功 `202` 并返回 `status=pending`。
- `GET /documents`、`GET /documents/{document_id}`：查询当前用户文档和异步状态。
- `DELETE /documents/{document_id}`：清理文件、向量和元数据，`204`，幂等。

## 问答

`POST /query` 请求：`{"session_id":"uuid","question":"购买后多久可以申请退款？"}`。问题长度 1-500，返回 `message_id`、`answer`、`answer_type`（`fqa`/`rag`/`fallback`）、来源、耗时和 warnings。

`POST /query/stream` 使用相同 JSON，并设置 `Accept: text/event-stream`：

```text
event: start
data: {"request_id":"uuid","message_id":"uuid"}
event: delta
data: {"text":"购买后"}
event: source
data: {"document_id":"uuid","document_name":"refund-policy.txt","excerpt":"..."}
event: done
data: {"message_id":"uuid","answer_type":"rag","retrieval_strategy":"hybrid_direct","latency_ms":42}
```

`delta` 可多次出现，`source` 在 `done` 前发送；异常返回 `event: error`，包含稳定错误码和 request_id。后端转发 Provider 实际流式片段，不伪造逐字符流。

## 健康检查

- `GET /health/live`：`{"status":"ok"}`，用于容器存活检查。
- 当前代码未实现独立 `/health/ready` 路由；启动顺序由 Compose 健康检查和依赖条件保证。
