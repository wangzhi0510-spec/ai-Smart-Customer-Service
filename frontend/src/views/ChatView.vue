<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import SessionSidebar from "../components/SessionSidebar.vue";
import MessageList from "../components/MessageList.vue";
import { useChatStore } from "../stores/chat";
import { useAuthStore } from "../stores/auth";

type Source = Record<string, any>;
type Message = { id: string; session_id?: string; role: string; content: string; status: string; sources: Source[] };
type EventData = { message_id?: string; text?: string; message?: string } & Source;
const chat = useChatStore();
const auth = useAuthStore();
const router = useRouter();
const sessions = ref<any[]>(chat.sessions ?? []);
const messages = ref<Message[]>((chat.messages ?? []) as Message[]);
const activeSessionId = ref<string | null>(sessions.value[0]?.id ?? null);
const question = ref("");
const lastQuestion = ref("");
const errorMessage = ref<string | null>(null);
const streamingId = ref<string | null>(null);
const canSubmit = computed(() => Boolean(activeSessionId.value && question.value.trim() && !chat.streaming));

onMounted(async () => {
  try {
    const loaded = await chat.listSessions();
    if (loaded?.length) sessions.value = loaded;
    if (!activeSessionId.value && sessions.value.length) activeSessionId.value = sessions.value[0].id;
    if (activeSessionId.value) messages.value = (await chat.loadMessages(activeSessionId.value)) as Message[];
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "会话加载失败"; }
});

async function selectSession(id: string) {
  activeSessionId.value = id;
  messages.value = (await chat.loadMessages(id)) as Message[];
}

async function createSession() {
  const created = await chat.createSession();
  sessions.value = chat.sessions ?? [...sessions.value, created];
  activeSessionId.value = created.id;
  messages.value = [];
}

async function removeSession(id: string) {
  await chat.deleteSession(id);
  sessions.value = (chat.sessions ?? sessions.value.filter((item) => item.id !== id)).filter((item) => item.id !== id);
  if (activeSessionId.value === id) {
    activeSessionId.value = sessions.value[0]?.id ?? null;
    messages.value = activeSessionId.value ? ((await chat.loadMessages(activeSessionId.value)) as Message[]) : [];
  }
}

async function submit() {
  if (!canSubmit.value || !activeSessionId.value) return;
  const text = question.value.trim();
  question.value = "";
  lastQuestion.value = text;
  errorMessage.value = null;
  const userMessage: Message = { id: `user-${Date.now()}`, session_id: activeSessionId.value, role: "user", content: text, status: "completed", sources: [] };
  const assistant: Message = { id: `pending-${Date.now()}`, session_id: activeSessionId.value, role: "assistant", content: "", status: "streaming", sources: [] };
  messages.value.push(userMessage, assistant);
  streamingId.value = assistant.id;
  try {
    await chat.streamQuestion(activeSessionId.value, text, (event) => {
      const data = (event.data && typeof event.data === "object" ? event.data : {}) as EventData;
      if (event.type === "start" && data.message_id) { assistant.id = data.message_id; streamingId.value = assistant.id; }
      if (event.type === "delta") assistant.content += String(data.text ?? "");
      if (event.type === "source") assistant.sources.push(data);
      if (event.type === "error") { assistant.status = "failed"; errorMessage.value = data.message ?? "问答失败"; }
      if (event.type === "done") assistant.status = "completed";
    });
    if (assistant.status === "streaming") assistant.status = "completed";
    const refreshed = await chat.loadMessages(activeSessionId.value);
    if (refreshed?.length) messages.value = refreshed as Message[];
  } catch (error) {
    assistant.status = "failed";
    errorMessage.value = error instanceof Error ? error.message : "连接中断，请重试";
  } finally { streamingId.value = null; }
}

async function retry() { if (lastQuestion.value) { question.value = lastQuestion.value; await submit(); } }
async function feedback(messageId: string, rating: "positive" | "negative") { await chat.submitFeedback(messageId, rating); }
function logout() { auth.logout(); void router.push("/login"); }
</script>

<template>
  <main class="app-shell">
    <SessionSidebar :sessions="sessions" :active-session-id="activeSessionId" @create="createSession" @select="selectSession" @remove="removeSession" />
    <section class="chat-workspace">
      <header class="topbar"><div><p class="eyebrow">AI 智能客服</p><h1>知识库问答工作台</h1></div><nav><router-link to="/documents">知识库</router-link><button type="button" class="link-button" @click="logout">退出</button></nav></header>
      <MessageList :messages="messages" :streaming-id="streamingId" @feedback="feedback" />
      <p v-if="errorMessage" role="alert" class="alert">{{ errorMessage }} <button type="button" @click="retry">重试</button></p>
      <form class="composer" @submit.prevent="submit"><label for="question">输入问题</label><textarea id="question" v-model="question" rows="3" maxlength="500" placeholder="请输入问题（最多 500 字）" :disabled="chat.streaming" /><div class="composer-footer"><span>{{ question.length }}/500</span><button type="submit" :disabled="!canSubmit">{{ chat.streaming ? "回答中…" : "发送" }}</button></div></form>
    </section>
  </main>
</template>
