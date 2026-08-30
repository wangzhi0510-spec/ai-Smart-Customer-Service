import { computed, ref } from "vue";
import { defineStore } from "pinia";

type AuthApi = { login: (identifier: string, password: string) => Promise<any>; register?: (identifier: string, password: string) => Promise<any> };
export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(globalThis.localStorage?.getItem("access_token") ?? null); const user = ref<any | null>(null); const isAuthenticated = computed(() => Boolean(token.value)); let api: AuthApi = { login: async (identifier, password) => (await fetch("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifier, password }) })).json() };
  function applyAuthResult(result: any) {
    if (typeof result?.access_token !== "string" || result.access_token.length === 0) throw new Error("INVALID_AUTH_RESPONSE");
    token.value = result.access_token;
    user.value = result.user;
    globalThis.localStorage?.setItem("access_token", result.access_token);
    return result;
  }
  async function login(identifier: string, password: string) { return applyAuthResult(await api.login(identifier, password)); }
  async function register(identifier: string, password: string) { if (!api.register) throw new Error("REGISTER_UNAVAILABLE"); return applyAuthResult(await api.register(identifier, password)); }
  function logout() { token.value = null; user.value = null; globalThis.localStorage?.removeItem("access_token"); }
  function setApi(value: AuthApi) { api = value; }
  return { token, user, isAuthenticated, login, register, logout, setApi };
});


