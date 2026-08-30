import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import LoginView from "../../src/views/LoginView.vue";
import RegisterView from "../../src/views/RegisterView.vue";
import { useAuthStore } from "../../src/stores/auth";
import { createPinia, setActivePinia } from "pinia";

describe("authentication views", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("validates login credentials before calling the auth API", async () => {
    const auth = useAuthStore();
    const login = vi.fn();
    auth.setApi({ login });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div />" } }, { path: "/login", component: { template: "<div />" } }, { path: "/register", component: { template: "<div />" } }] });
    const wrapper = mount(LoginView, { global: { plugins: [router] } });
    await wrapper.get("form").trigger("submit");
    expect(login).not.toHaveBeenCalled();
    expect(wrapper.get("[role='alert']").text()).toContain("至少 8 位密码");
  });

  it("submits registration and navigates to chat", async () => {
    const auth = useAuthStore();
    auth.setApi({ login: vi.fn(), register: vi.fn().mockResolvedValue({ access_token: "token-1", user: { id: "u1" } }) });
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div />" } }, { path: "/login", component: { template: "<div />" } }, { path: "/chat", component: { template: "<div />" } }] });
    const wrapper = mount(RegisterView, { global: { plugins: [router] } });
    await wrapper.get("#register-identifier").setValue("u@example.com");
    await wrapper.get("#register-password").setValue("password1");
    await wrapper.get("#register-confirm").setValue("password1");
    await wrapper.get("form").trigger("submit");
    await router.isReady();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(auth.token).toBe("token-1");
    expect(router.currentRoute.value.path).toBe("/chat");
  });
});
