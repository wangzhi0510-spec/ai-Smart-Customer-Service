import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import ChatView from "../views/ChatView.vue";
import DocumentsView from "../views/DocumentsView.vue";
export const router = createRouter({ history: createWebHistory(), routes: [
  { path: "/", redirect: "/chat" }, { path: "/login", component: LoginView }, { path: "/register", component: RegisterView },
  { path: "/chat", component: ChatView, meta: { requiresAuth: true } },
  { path: "/documents", component: DocumentsView, meta: { requiresAuth: true } },
] });
router.beforeEach((to) => { if (to.meta.requiresAuth && !localStorage.getItem("access_token")) return "/login"; if (to.path === "/login" && localStorage.getItem("access_token")) return "/chat"; return true; });
