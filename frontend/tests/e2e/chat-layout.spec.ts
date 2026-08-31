import { expect, test } from "@playwright/test";

test("桌面端会话栏与聊天内容独立滚动", async ({ page }) => {
  const user = { id: "layout-user", email: "layout@example.com", phone: null, status: "active" };
  const sessions = Array.from({ length: 40 }, (_, index) => ({ id: `session-${index}`, title: `会话 ${index + 1}` }));
  const messages = Array.from({ length: 50 }, (_, index) => ({
    id: `message-${index}`,
    session_id: "session-0",
    role: index % 2 ? "user" : "assistant",
    content: `第 ${index + 1} 条用于验证独立滚动的较长消息内容。`.repeat(3),
    status: "completed",
    sources: [],
  }));

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (body: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (path === "/api/v1/auth/register") return json({ access_token: "layout-token", token_type: "bearer", user }, 201);
    if (path === "/api/v1/sessions") return json(sessions);
    if (path === "/api/v1/sessions/session-0/messages") return json(messages);
    return json({ error: { code: "NOT_FOUND", message: "mock route not found", details: {} } }, 404);
  });

  await page.goto("/register");
  await page.locator("#register-identifier").fill(user.email);
  await page.locator("#register-password").fill("password1");
  await page.locator("#register-confirm").fill("password1");
  await page.getByRole("button", { name: "注册" }).click();
  await expect(page).toHaveURL(/\/chat$/);
  await page.locator(".message").first().waitFor();

  const before = await page.evaluate(() => {
    const sidebar = document.querySelector<HTMLElement>(".session-sidebar")!;
    const sessionList = document.querySelector<HTMLElement>(".session-list")!;
    const messageList = document.querySelector<HTMLElement>(".message-list")!;
    return {
      bodyScrollHeight: document.body.scrollHeight,
      viewportHeight: window.innerHeight,
      sidebarTop: sidebar.getBoundingClientRect().top,
      sessionOverflowY: getComputedStyle(sessionList).overflowY,
      sessionScrollHeight: sessionList.scrollHeight,
      sessionClientHeight: sessionList.clientHeight,
      messageOverflowY: getComputedStyle(messageList).overflowY,
      messageScrollHeight: messageList.scrollHeight,
      messageClientHeight: messageList.clientHeight,
    };
  });

  expect(before.bodyScrollHeight).toBeLessThanOrEqual(before.viewportHeight + 1);
  expect(before.sessionOverflowY).toBe("auto");
  expect(before.sessionScrollHeight).toBeGreaterThan(before.sessionClientHeight);
  expect(before.messageOverflowY).toBe("auto");
  expect(before.messageScrollHeight).toBeGreaterThan(before.messageClientHeight);

  await page.evaluate(() => {
    const list = document.querySelector<HTMLElement>(".message-list")!;
    list.scrollTop = 500;
  });

  const after = await page.evaluate(() => ({
    sidebarTop: document.querySelector<HTMLElement>(".session-sidebar")!.getBoundingClientRect().top,
    messageScrollTop: document.querySelector<HTMLElement>(".message-list")!.scrollTop,
    windowScrollY: window.scrollY,
  }));

  expect(after.messageScrollTop).toBeGreaterThan(0);
  expect(after.sidebarTop).toBeCloseTo(before.sidebarTop, 0);
  expect(after.windowScrollY).toBe(0);
});

test("桌面端知识库长列表保持页面自然滚动", async ({ page }) => {
  const user = { id: "documents-user", email: "documents@example.com", phone: null, status: "active" };
  const documents = Array.from({ length: 40 }, (_, index) => ({
    id: `document-${index}`,
    original_name: `知识文档-${index + 1}.txt`,
    media_type: "text/plain",
    size_bytes: 1024,
    content_sha256: "a".repeat(64),
    status: "ready",
    version: 1,
    chunk_count: 1,
    error_code: null,
    created_at: "2026-08-31T00:00:00Z",
    updated_at: "2026-08-31T00:00:00Z",
  }));

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (body: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/v1/auth/register") return json({ access_token: "documents-token", token_type: "bearer", user }, 201);
    if (path === "/api/v1/sessions") return json([]);
    if (path === "/api/v1/documents") return json(documents);
    return json({ error: { code: "NOT_FOUND", message: "mock route not found", details: {} } }, 404);
  });

  await page.goto("/register");
  await page.locator("#register-identifier").fill(user.email);
  await page.locator("#register-password").fill("password1");
  await page.locator("#register-confirm").fill("password1");
  await page.getByRole("button", { name: "注册" }).click();
  await page.getByRole("link", { name: "知识库" }).click();
  await expect(page).toHaveURL(/\/documents$/);
  await expect(page.getByText("知识文档-40.txt")).toBeVisible();

  const dimensions = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    viewportHeight: window.innerHeight,
    shellOverflowY: getComputedStyle(document.querySelector<HTMLElement>(".single-page")!).overflowY,
  }));
  expect(dimensions.bodyScrollHeight).toBeGreaterThan(dimensions.viewportHeight);
  expect(dimensions.shellOverflowY).toBe("visible");
});

test("移动端恢复单栏自然滚动", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 720 });
  const user = { id: "mobile-user", email: "mobile@example.com", phone: null, status: "active" };
  const messages = Array.from({ length: 30 }, (_, index) => ({
    id: `mobile-message-${index}`,
    session_id: "mobile-session",
    role: "assistant",
    content: `移动端第 ${index + 1} 条较长消息。`.repeat(8),
    status: "completed",
    sources: [],
  }));

  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (body: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/v1/auth/register") return json({ access_token: "mobile-token", token_type: "bearer", user }, 201);
    if (path === "/api/v1/sessions") return json([{ id: "mobile-session", title: "移动端测试" }]);
    if (path === "/api/v1/sessions/mobile-session/messages") return json(messages);
    return json({ error: { code: "NOT_FOUND", message: "mock route not found", details: {} } }, 404);
  });

  await page.goto("/register");
  await page.locator("#register-identifier").fill(user.email);
  await page.locator("#register-password").fill("password1");
  await page.locator("#register-confirm").fill("password1");
  await page.getByRole("button", { name: "注册" }).click();
  await expect(page).toHaveURL(/\/chat$/);
  await page.locator(".message").first().waitFor();

  const layout = await page.evaluate(() => ({
    display: getComputedStyle(document.querySelector<HTMLElement>(".app-shell")!).display,
    bodyScrollHeight: document.body.scrollHeight,
    viewportHeight: window.innerHeight,
    messageOverflowY: getComputedStyle(document.querySelector<HTMLElement>(".message-list")!).overflowY,
    sessionOverflowX: getComputedStyle(document.querySelector<HTMLElement>(".session-list")!).overflowX,
  }));

  expect(layout.display).toBe("block");
  expect(layout.bodyScrollHeight).toBeGreaterThan(layout.viewportHeight);
  expect(layout.messageOverflowY).toBe("visible");
  expect(layout.sessionOverflowX).toBe("auto");
});
