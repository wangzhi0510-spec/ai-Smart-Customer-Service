<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import DocumentStatus from "../components/DocumentStatus.vue";
import DocumentUploader from "../components/DocumentUploader.vue";
import { useDocumentsStore } from "../stores/documents";
const router = useRouter(); const documentsStore = useDocumentsStore(); const documents = computed(() => documentsStore.documents ?? []); const errorMessage = ref<string | null>(null); let poller: ReturnType<typeof setInterval> | undefined;
async function refresh() { try { await documentsStore.list(); errorMessage.value = null; } catch (cause) { errorMessage.value = cause instanceof Error ? cause.message : "文档列表加载失败"; } }
async function upload(file: File) { try { await documentsStore.upload(file); await refresh(); } catch (cause) { errorMessage.value = cause instanceof Error ? cause.message : "上传失败"; } }
async function remove(id: string) { if (!window.confirm("确定删除该文档吗？删除后将无法用于问答。")) return; try { await documentsStore.remove(id); } catch (cause) { errorMessage.value = cause instanceof Error ? cause.message : "删除失败"; } }
function uploaderError(message: string) { errorMessage.value = message; }
onMounted(() => { void refresh(); poller = setInterval(() => { if (documents.value.some((item: any) => item.status === "pending" || item.status === "processing")) void refresh(); }, 5000); });
onUnmounted(() => { if (poller) clearInterval(poller); });
</script>
<template><main class="app-shell single-page"><section class="chat-workspace"><header class="topbar"><div><p class="eyebrow">知识库</p><h1>知识库管理</h1></div><button type="button" class="link-button" @click="router.push('/chat')">返回聊天</button></header><section class="documents-page"><DocumentUploader @upload="upload" @error="uploaderError" /><p v-if="errorMessage" role="alert" class="alert">{{ errorMessage }} <button type="button" @click="refresh">重试</button></p><div v-if="documentsStore.loading" class="empty-state" aria-busy="true">正在加载文档…</div><div v-else-if="documents.length === 0" class="empty-state"><h2>还没有知识文档</h2><p>上传产品政策、帮助文档或常见问题，开始构建知识库。</p></div><ul v-else class="document-list"><li v-for="document in documents" :key="document.id" class="document-row"><div class="document-main"><strong>{{ document.original_name }}</strong><span class="document-meta">{{ document.size_bytes }} 字节 · {{ document.chunk_count ?? 0 }} 个块</span></div><DocumentStatus :status="document.status" :error-code="document.error_code" /><button type="button" class="delete-button light" :data-document-id="document.id" aria-label="删除文档" @click="remove(document.id)">删除</button></li></ul></section></section></main></template>
