<script setup lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>

<template><main class="app-shell single-page"><section class="chat-workspace"><header class="topbar"><div><p class="eyebrow">知识库</p><h1>知识库管理</h1></div><button type="button" class="link-button" @click="router.push('/chat')">返回聊天</button></header><section class="empty-state"><h2>文档管理即将启用</h2><p>上传、状态轮询和删除将在任务 16 完成。当前保留真实路由边界。</p></section></section></main></template>
