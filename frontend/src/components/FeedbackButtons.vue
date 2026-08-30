<script setup lang="ts">
defineProps<{ disabled?: boolean }>();
const emit = defineEmits<{ feedback: [rating: "positive" | "negative"] }>();
</script>

<template>
  <div class="feedback-buttons" aria-label="回答反馈">
    <button type="button" aria-label="赞同回答" :disabled="disabled" @click="emit('feedback', 'positive')">赞</button>
    <button type="button" aria-label="不满意回答" :disabled="disabled" @click="emit('feedback', 'negative')">踩</button>
  </div>
</template>
