import { expect, test } from "@playwright/test";

const user = { id: "user-1", email: "browser@example.com", phone: null, status: "active" };
const session = { id: "session-1", title: "新会话", is_deleted: false, created_at: "2026-08-31T00:00:00Z", updated_at: "2026-08-31T00:00:00Z" };
const document = {
  id: "document-1", original_name: "refund-policy.txt", media_type: "text/plain", size_bytes: 38,
  content_sha256: "a".repeat(64), status: "ready", version: 1, chunk_count: 1,
  error_code: null, created_at: "2026-08-31T00:00:00Z", updated_at: "2026-08-31T00:00:00Z",
};

test("核心闭环：注册、登录、上传、SSE 来源、反馈、删除后不可检索", async ({ page }) => {
  let deleted = false;
  let hasSession = false;
  let hasAnswer = false;

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const json = (body: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (path === "/api/v1/auth/register" && method === "POST") return json({ access_token: "token-1", token_type: "bearer", user }, 201);
    if (path === "/api/v1/auth/login" && method === "POST") return json({ access_token: "token-2", token_type: "bearer", user });
    if (path === "/api/v1/sessions" && method === "GET") return json(hasSession ? [session] : []);
    if (path === "/api/v1/sessions" && method === "POST") { hasSession = true; return json(session, 201); }
    if (path === "/api/v1/sessions/session-1/messages" && method === "GET") {
      return json(hasAnswer ? [{ id: "message-1", session_id: session.id, role: "assistant", content: "Refunds are available within 30 days.", status: "completed", answer_type: "rag", retrieval_strategy: "hybrid_direct", latency_ms: 4, created_at: session.created_at, sources: [{ id: "source-1", document_id: document.id, document_name: document.original_name, page_number: 1, section_title: "Refunds", excerpt: "Refunds are available within 30 days.", display_order: 1 }] }] : []);
    }
    if (path === "/api/v1/documents" && method === "GET") return json(deleted ? [] : [document]);
    if (path === "/api/v1/documents" && method === "POST") return json(document, 202);
    if (path === "/api/v1/documents/document-1" && method === "DELETE") { deleted = true; return route.fulfill({ status: 204 }); }
    if (path === "/api/v1/messages/message-1/feedback" && method === "PUT") return json({ id: "feedback-1", message_id: "message-1", user_id: user.id, rating: "positive", comment: null, created_at: session.created_at, updated_at: session.updated_at });
    if (path === "/api/v1/query/stream" && method === "POST") {
      hasAnswer = !deleted;
      const body = deleted
        ? "event: start\ndata: {\"request_id\":\"req-2\",\"message_id\":\"message-2\"}\n\nevent: delta\ndata: {\"text\":\"知识库暂无足够信息回答该问题。\"}\n\nevent: done\ndata: {\"message_id\":\"message-2\",\"answer_type\":\"fallback\",\"retrieval_strategy\":\"hybrid_direct\",\"latency_ms\":2}\n\n"
        : "event: start\ndata: {\"request_id\":\"req-1\",\"message_id\":\"message-1\"}\n\nevent: delta\ndata: {\"text\":\"Refunds are available within 30 days.\"}\n\nevent: source\ndata: {\"document_id\":\"document-1\",\"document_name\":\"refund-policy.txt\",\"page_number\":1,\"section_title\":\"Refunds\",\"excerpt\":\"Refunds are available within 30 days.\"}\n\nevent: done\ndata: {\"message_id\":\"message-1\",\"answer_type\":\"rag\",\"retrieval_strategy\":\"hybrid_direct\",\"latency_ms\":4}\n\n";
      return route.fulfill({ status: 200, contentType: "text/event-stream", body });
    }
    return json({ error: { code: "NOT_FOUND", message: "mock route not found", details: {} } }, 404);
  });

  await page.goto("/register");
  await page.locator("#register-identifier").fill("browser@example.com");
  await page.locator("#register-password").fill("password1");
  await page.locator("#register-confirm").fill("password1");
  await page.getByRole("button", { name: "注册" }).click();
  await expect(page).toHaveURL(/\/chat$/);

  await page.getByRole("button", { name: "退出" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.locator("#login-identifier").fill("browser@example.com");
  await page.locator("#login-password").fill("password1");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page).toHaveURL(/\/chat$/);
  await page.getByRole("button", { name: "新建会话" }).click();
  await expect(page.locator(".session-item")).toHaveCount(1);

  await page.getByRole("link", { name: "知识库" }).click();
  await expect(page).toHaveURL(/\/documents$/);
  await expect(page.getByText("refund-policy.txt")).toBeVisible();
  await expect(page.getByLabel("已就绪")).toBeVisible();
  const chooser = page.waitForEvent("filechooser");
  await page.locator("#document-file").click();
  await (await chooser).setFiles({ name: "refund-policy.txt", mimeType: "text/plain", buffer: Buffer.from("Refunds are available within 30 days.") });
  await expect(page.getByText("refund-policy.txt")).toBeVisible();

  await page.getByRole("button", { name: "返回聊天" }).click();
  await page.locator("#question").fill("What is the refund period?");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.locator(".message.assistant .message-content").filter({ hasText: "Refunds are available within 30 days." })).toBeVisible();
  await page.getByText(/来源（1）/).click();
  await expect(page.locator(".sources")).toContainText("refund-policy.txt");
  await expect(page.locator(".sources")).toContainText("Refunds are available within 30 days.");
  await page.getByRole("button", { name: "赞同回答" }).click();

  await page.getByRole("link", { name: "知识库" }).click();
  page.on("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "删除文档" }).click();
  await expect(page.getByText("还没有知识文档")).toBeVisible();

  await page.getByRole("button", { name: "返回聊天" }).click();
  await page.locator("#question").fill("What is the refund period?");
  await page.getByRole("button", { name: "发送" }).click();
  await expect(page.getByText("知识库暂无足够信息回答该问题。", { exact: true })).toBeVisible();
  await expect(page.locator(".message.assistant").last().locator(".sources")).toHaveCount(0);
});
