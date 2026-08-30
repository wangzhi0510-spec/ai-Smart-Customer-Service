<script setup lang="ts">
defineProps<{ sessions: Array<{ id: string; title: string }>; activeSessionId: string | null }>();
const emit = defineEmits<{ create: []; select: [id: string]; remove: [id: string] }>();
</script>

<template>
  <aside class="session-sidebar" data-testid="session-sidebar" aria-label="会话列表">
    <div class="sidebar-heading">
      <h2>会话</h2>
      <button type="button" aria-label="新建会话" class="icon-button" @click="emit('create')">+</button>
    </div>
    <p v-if="sessions.length === 0" class="empty-hint">还没有会话</p>
    <ul v-else class="session-list">
      <li v-for="session in sessions" :key="session.id">
        <button type="button" class="session-item" :class="{ active: session.id === activeSessionId }" :data-session-id="session.id" @click="emit('select', session.id)">
          <span>{{ session.title }}</span>
        </button>
        <button type="button" aria-label="删除会话" class="delete-button" @click.stop="emit('remove', session.id)">×</button>
      </li>
    </ul>
  </aside>
</template>
