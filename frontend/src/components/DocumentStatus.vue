<script setup lang="ts">
defineProps<{ status: string; errorCode?: string | null }>();
const labels: Record<string, string> = { pending: "待处理", processing: "处理中", ready: "已就绪", failed: "处理失败" };
</script>
<template><span class="document-status" :class="'status-' + status" :aria-label="labels[status] ?? status">{{ labels[status] ?? status }}<span v-if="status === 'failed' && errorCode">：{{ errorCode }}</span></span></template>
