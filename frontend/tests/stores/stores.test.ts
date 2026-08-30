import { describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAuthStore } from "../../src/stores/auth";

describe("auth store", () => {
  it("stores token after login and clears it on logout", async () => {
    setActivePinia(createPinia());
    const api = { login: vi.fn().mockResolvedValue({ access_token: "abc", user: { id: "u1" } }) };
    const store = useAuthStore();
    store.setApi(api);

    await store.login("u@example.com", "password");
    expect(store.token).toBe("abc");
    store.logout();
    expect(store.token).toBeNull();
  });
});


