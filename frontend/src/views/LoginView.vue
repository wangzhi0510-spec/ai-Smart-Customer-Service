<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
const auth = useAuthStore();
const router = useRouter();
const identifier = ref("");
const password = ref("");
const error = ref<string | null>(null);
const submitting = ref(false);
async function submit() {
  error.value = null;
  if (!identifier.value.trim() || password.value.length < 8) { error.value = "请输入邮箱或手机号，以及至少 8 位密码"; return; }
  submitting.value = true;
  try { await auth.login(identifier.value, password.value); await router.push("/chat"); }
  catch (cause) { error.value = cause instanceof Error ? cause.message : "登录失败，请重试"; }
  finally { submitting.value = false; }
}
</script>

<template>
  <main class="auth-shell"><section class="auth-card"><p class="eyebrow">AI 智能客服</p><h1>登录工作台</h1><p class="muted">使用邮箱或中国大陆手机号继续</p><form @submit.prevent="submit"><label for="login-identifier">邮箱或手机号</label><input id="login-identifier" v-model="identifier" autocomplete="username" required /><label for="login-password">密码</label><input id="login-password" v-model="password" type="password" minlength="8" autocomplete="current-password" required /><p v-if="error" role="alert" class="alert">{{ error }}</p><button type="submit" :disabled="submitting">{{ submitting ? "登录中…" : "登录" }}</button></form><router-link to="/register">还没有账号？注册</router-link></section></main>
</template>
