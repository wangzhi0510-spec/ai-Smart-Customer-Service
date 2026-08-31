# Frontend

Vue 3 + TypeScript + Vite + Pinia 客服工作台。前端只调用后端 REST 和 POST-SSE，不保存或调用 LLM API Key。

## 本地运行

```powershell
cd D:\code\codex_code\cs_rag_agent\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

页面路由：

- `/login`：登录
- `/register`：注册
- `/chat`：会话、流式问答、来源和反馈
- `/documents`：知识文档上传、状态和删除

## 测试和构建

```powershell
npm test -- --run
npm run build
npx playwright test --config playwright.config.ts
```

Playwright 测试使用 API route mock 验证浏览器交互和 SSE 契约；真实后端联调按部署文档启动 API 与基础设施。

## 代码边界

- `src/api/http.ts`：Bearer、JSON、错误和 204 处理
- `src/api/queryStream.ts`：fetch 流读取和 SSE 多行 data 解析
- `src/stores`：认证、会话和文档状态
- `src/views`、`src/components`：页面和可访问 UI
- `tests`：Vitest 与 Playwright

路由守卫使用 `localStorage.access_token` 判断登录态；401 时应清理登录态并回到登录页。上传使用 `FormData`，不手动设置 multipart boundary。