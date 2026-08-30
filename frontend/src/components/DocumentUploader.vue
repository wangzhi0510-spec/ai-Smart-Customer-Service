<script setup lang="ts">
import { ref } from "vue";
const emit = defineEmits<{ upload: [file: File]; error: [message: string] }>();
const input = ref<HTMLInputElement | null>(null); const allowed = new Set(["txt", "md", "pdf"]); const maxBytes = 20 * 1024 * 1024;
function selectFile(event: Event) { const file = (event.target as HTMLInputElement).files?.[0]; if (!file) return; const ext = file.name.split(".").pop()?.toLowerCase() ?? ""; if (!allowed.has(ext)) { emit("error", "仅支持 TXT、MD 和 PDF 文件"); return; } if (file.size === 0) { emit("error", "文件不能为空"); return; } if (file.size > maxBytes) { emit("error", "文件大小不能超过 20 MiB"); return; } emit("upload", file); if (input.value) input.value.value = ""; }
</script>
<template><section class="document-uploader"><label for="document-file">上传知识文档</label><input id="document-file" ref="input" type="file" accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf" @change="selectFile" /><p class="muted">支持 TXT、MD、PDF，单文件不超过 20 MiB</p></section></template>
