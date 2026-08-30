import { createRouter, createWebHistory } from "vue-router";
export const router = createRouter({ history: createWebHistory(), routes: [
  { path: "/", redirect: "/chat" }, { path: "/login", component: { template: "<main><h1>登录</h1></main>" } },
  { path: "/chat", component: { template: "<main><h1>智能客服</h1></main>" }, meta: { requiresAuth: true } },
  { path: "/documents", component: { template: "<main><h1>知识库</h1></main>" }, meta: { requiresAuth: true } },
] });
router.beforeEach((to) => { if (to.meta.requiresAuth && !localStorage.getItem("access_token")) return "/login"; if (to.path === "/login" && localStorage.getItem("access_token")) return "/chat"; return true; });

