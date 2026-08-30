import { ref } from "vue";
import { defineStore } from "pinia";
import { parseSSEStream, type SSEEvent } from "../api/queryStream";
export const useChatStore = defineStore("chat", () => {
  const sessions = ref<any[]>([]); const messages = ref<any[]>([]); const streaming = ref(false); const error = ref<string | null>(null);
  async function createSession(title = "新会话") { const response = await fetch("/api/v1/sessions", { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ title }) }); const item = await response.json(); sessions.value.unshift(item); return item; }
  async function loadMessages(sessionId: string) { const response = await fetch(`/api/v1/sessions/${sessionId}/messages`, { headers: authHeaders() }); messages.value = await response.json(); return messages.value; }
  async function streamQuestion(sessionId: string, question: string, onEvent: (event: SSEEvent) => void) { streaming.value = true; error.value = null; try { const response = await fetch("/api/v1/query/stream", { method: "POST", headers: { ...authHeaders(), Accept: "text/event-stream", "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sessionId, question }) }); await parseSSEStream(response, onEvent); } catch (cause) { error.value = cause instanceof Error ? cause.message : "连接失败"; throw cause; } finally { streaming.value = false; } }
  function authHeaders(): Record<string, string> { const token = localStorage.getItem("access_token"); return token ? { Authorization: `Bearer ${token}` } : {}; }
  return { sessions, messages, streaming, error, createSession, loadMessages, streamQuestion };
});

