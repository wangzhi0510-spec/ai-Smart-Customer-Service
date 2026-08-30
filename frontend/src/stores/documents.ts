import { ref } from "vue";
import { defineStore } from "pinia";
export const useDocumentsStore = defineStore("documents", () => {
  const documents = ref<any[]>([]); const loading = ref(false); const error = ref<string | null>(null);
  async function list() { loading.value = true; try { const response = await fetch("/api/v1/documents", { headers: authHeaders() }); documents.value = await response.json(); return documents.value; } finally { loading.value = false; } }
  async function upload(file: File) { const form = new FormData(); form.append("file", file); const response = await fetch("/api/v1/documents", { method: "POST", headers: authHeaders(), body: form }); if (!response.ok) throw new Error("UPLOAD_FAILED"); const item = await response.json(); documents.value.unshift(item); return item; }
  async function remove(id: string) { const response = await fetch(`/api/v1/documents/${id}`, { method: "DELETE", headers: authHeaders() }); if (!response.ok) throw new Error("DELETE_FAILED"); documents.value = documents.value.filter((item) => item.id !== id); }
  function authHeaders(): Record<string, string> { const token = localStorage.getItem("access_token"); return token ? { Authorization: `Bearer ${token}` } : {}; }
  return { documents, loading, error, list, upload, remove };
});
