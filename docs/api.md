# API 文档

基础前缀：`/api/v1`。除健康检查外均需 `Authorization: Bearer <access_token>`。

## 1. 统一错误

JSON 错误结构：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数无效",
    "details": {},
    "request_id": "uuid"
  }
}
```

常见错误码：`VALIDATION_ERROR`、`UNAUTHORIZED`、`NOT_FOUND`、`FORBIDDEN`、`QUOTA_EXCEEDED`、`UNSUPPORTED_FILE_TYPE`、`DUPLICATE_DOCUMENT`、`QA_UNAVAILABLE`、`QA_FAILED`、`DOCUMENT_CREATE_ERROR`、`DOCUMENT_DELETE_ERROR`。

## 2. 认证

### `POST /auth/register`

请求：

```json
{"identifier":"user@example.com","password":"至少 8 位密码"}
```

支持邮箱或中国大陆手机号。成功返回 `201`：

```json
{"access_token":"<token>","token_type":"bearer","user":{"id":"uuid","email":"user@example.com","phone":null,"status":"active"}}
```

### `POST /auth/login`

请求字段与注册相同，成功返回 `200`，响应结构相同。

### `GET /auth/me`

返回当前 Token 用户：

```json
{"id":"uuid","email":"user@example.com","phone":null,"status":"active"}
```

## 3. 会话和消息

### `POST /sessions`

请求：`{"title":"售后咨询"}`，成功 `201` 返回会话 ID、标题、删除标记和 UTC 时间。

### `GET /sessions?page=1&page_size=20`

返回当前用户未删除会话列表。`page_size` 范围为 1-100。

### `GET /sessions/{session_id}`

返回会话详情；访问其他用户会话返回 `404`。

### `DELETE /sessions/{session_id}`

软删除会话，成功 `204 No Content`。

### `GET /sessions/{session_id}/messages`

返回按创建时间升序排列的消息：

```json
[{"id":"uuid","session_id":"uuid","role":"assistant","content":"回答","answer_type":"rag","retrieval_strategy":"hybrid_direct","status":"completed","latency_ms":42,"created_at":"2026-08-31T05:00:00Z","sources":[]}]
```

### `PUT /messages/{message_id}/feedback`

请求：`{"rating":"positive","comment":"有帮助"}`。`rating` 只能是 `positive` 或 `negative`；同一用户对同一 assistant 消息重复提交会更新原反馈。

## 4. 文档

### `POST /documents`

使用 `multipart/form-data`，字段名为 `file`。支持 `.txt`、`.md`、`.pdf`，默认上限 20 MiB。成功返回 `202`：

```json
{"id":"uuid","original_name":"refund-policy.txt","media_type":"text/plain","size_bytes":1234,"content_sha256":"sha256","status":"pending","version":1,"chunk_count":0,"error_code":null,"created_at":"2026-08-31T05:00:00Z","updated_at":"2026-08-31T05:00:00Z"}
```

### `GET /documents`

返回当前用户未删除文档及其异步状态。

### `GET /documents/{document_id}`

返回文档详情；其他用户不可见。

### `DELETE /documents/{document_id}`

清理存储文件并软删除元数据，成功 `204`。重复删除保持幂等。

## 5. 非流式问答

### `POST /query`

请求：

```json
{"session_id":"uuid","question":"购买后多久可以申请退款？"}
```

`question` 长度 1-500。响应：

```json
{"message_id":"uuid","answer":"购买后七天内可以申请退款。","answer_type":"rag","retrieval_strategy":"hybrid_direct","sources":[{"document_id":"uuid","document_name":"refund-policy.txt","page_number":null,"section_title":null,"excerpt":"退款政策...","retrieval_score":0.91}],"latency_ms":42,"warnings":[]}
```

`answer_type`：`fqa`、`rag` 或 `fallback`。无充分证据时返回标准 fallback，不调用 LLM。

## 6. POST-SSE 流式问答

### `POST /query/stream`

请求体同 `/query`，请求头增加 `Accept: text/event-stream`。事件格式：

```text
event: start
data: {"request_id":"uuid","message_id":"uuid"}

event: delta
data: {"text":"购买后"}

event: source
data: {"document_id":"uuid","document_name":"refund-policy.txt","page_number":null,"section_title":null,"excerpt":"..."}

event: done
data: {"message_id":"uuid","answer_type":"rag","retrieval_strategy":"hybrid_direct","latency_ms":42}
```

`delta` 可出现多次，`source` 在 `done` 前发送。异常返回：

```text
event: error
data: {"code":"QA_FAILED","message":"问答服务暂时不可用","details":{},"request_id":"uuid"}
```

后端直接转发 Provider 的流式片段；客户端应持续读取，直到 `done` 或 `error`。

## 7. 健康检查

- `GET /health/live`：返回 `{"status":"ok"}`，用于容器存活检查。

当前代码未实现独立的 `/health/ready` 路由；生产编排通过 Compose `depends_on` 和后端存活检查保证启动顺序。