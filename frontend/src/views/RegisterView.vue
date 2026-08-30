<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
const auth = useAuthStore();
const router = useRouter();
const identifier = ref(""); const password = ref(""); const confirmPassword = ref(""); const error = ref<string | null>(null); const submitting = ref(false);
async function submit() {
  error.value = null;
  if (!identifier.value.trim() || password.value.length < 8) { error.value = "请输入有效标识和至少 8 位密码"; return; }
  if (password.value !== confirmPassword.value) { error.value = "两次输入的密码不一致"; return; }
  submitting.value = true;
  try { await auth.register(identifier.value, password.value); await router.push("/chat"); }
  catch (cause) { error.value = cause instanceof Error ? cause.message : "注册失败，请重试"; }
  finally { submitting.value = false; }
}
</script>

<template>
  <main class="auth-shell"><section class="auth-card"><p class="eyebrow">AI 智能客服</p><h1>创建账号</h1><p class="muted">注册后即可使用知识库问答</p><form @submit.prevent="submit"><label for="register-identifier">邮箱或手机号</label><input id="register-identifier" v-model="identifier" autocomplete="username" required /><label for="register-password">密码</label><input id="register-password" v-model="password" type="password" minlength="8" autocomplete="new-password" required /><label for="register-confirm">确认密码</label><input id="register-confirm" v-model="confirmPassword" type="password" minlength="8" autocomplete="new-password" required /><p v-if="error" role="alert" class="alert">{{ error }}</p><button type="submit" :disabled="submitting">{{ submitting ? "注册中…" : "注册" }}</button></form><router-link to="/login">已有账号？登录</router-link></section></main>
</template>
