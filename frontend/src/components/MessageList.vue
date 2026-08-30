<script setup lang="ts">
import SourceCitations from "./SourceCitations.vue";
import FeedbackButtons from "./FeedbackButtons.vue";

type Message = { id: string; role: string; content: string; status?: string; sources?: Array<Record<string, unknown>> };
defineProps<{ messages: Message[]; streamingId?: string | null }>();
const emit = defineEmits<{ feedback: [messageId: string, rating: "positive" | "negative"] }>();
</script>

<template>
  <section class="message-list" aria-live="polite" aria-label="聊天消息">
    <div v-if="messages.length === 0" class="empty-state"><h2>开始一次咨询</h2><p>请输入问题，客服会基于知识库为你回答。</p></div>
    <article v-for="message in messages" :key="message.id" class="message" :class="message.role">
      <div class="message-role">{{ message.role === "user" ? "你" : "AI 客服" }}</div>
      <p class="message-content">{{ message.content || (message.status === "streaming" ? "正在思考…" : "") }}</p>
      <span v-if="message.status === 'failed'" class="message-error">本次回答未完成</span>
      <SourceCitations v-if="message.role === 'assistant'" :sources="message.sources ?? []" />
      <FeedbackButtons v-if="message.role === 'assistant' && message.status === 'completed'" @feedback="(rating) => emit('feedback', message.id, rating)" />
    </article>
  </section>
</template>
