<script setup lang="ts">
import { ref } from "vue";

defineProps<{ sessions: Array<{ id: string; title: string }>; activeSessionId: string | null }>();
const emit = defineEmits<{
  create: [];
  select: [id: string];
  remove: [id: string];
  rename: [id: string, title: string];
}>();
const editingId = ref<string | null>(null);
const editingTitle = ref("");
const saving = ref(false);

function beginRename(session: { id: string; title: string }) {
  editingId.value = session.id;
  editingTitle.value = session.title;
}

function cancelRename() {
  editingId.value = null;
  editingTitle.value = "";
}

async function saveRename(id: string) {
  if (saving.value || editingId.value !== id) return;
  const title = editingTitle.value.trim();
  if (!title) return;
  saving.value = true;
  try {
    emit("rename", id, title);
    cancelRename();
  } finally {
    saving.value = false;
  }
}
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
        <template v-if="editingId === session.id">
          <input v-model="editingTitle" class="session-title-input" aria-label="会话名称" maxlength="255" @keydown.enter.prevent="saveRename(session.id)" @keydown.esc.prevent="cancelRename" @blur="saveRename(session.id)" />
        </template>
        <button v-else type="button" class="session-item" :class="{ active: session.id === activeSessionId }" :data-session-id="session.id" @click="emit('select', session.id)">
          <span>{{ session.title }}</span>
        </button>
        <button v-if="editingId !== session.id" type="button" aria-label="重命名会话" class="rename-button" @click.stop="beginRename(session)">✎</button>
        <button v-if="editingId !== session.id" type="button" aria-label="删除会话" class="delete-button" @click.stop="emit('remove', session.id)">×</button>
      </li>
    </ul>
  </aside>
</template>
