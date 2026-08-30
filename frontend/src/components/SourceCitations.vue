<script setup lang="ts">
defineProps<{ sources: Array<{ id?: string; document_name?: string; page_number?: number | null; section_title?: string | null; excerpt?: string }> }>();
</script>

<template>
  <details v-if="sources.length" class="sources">
    <summary>来源（{{ sources.length }}）</summary>
    <ol>
      <li v-for="source in sources" :key="source.id ?? source.document_name">
        <strong>{{ source.document_name }}</strong>
        <span v-if="source.page_number"> · 第 {{ source.page_number }} 页</span>
        <span v-if="source.section_title"> · {{ source.section_title }}</span>
        <p>{{ source.excerpt }}</p>
      </li>
    </ol>
  </details>
</template>
