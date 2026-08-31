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

  it("registers through the default auth API", async () => {
    setActivePinia(createPinia());
    const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access_token: "reg-token", user: { id: "u2" } }), { status: 201 }),
    );
    const store = useAuthStore();

    await store.register("new@example.com", "password1");

    expect(fetcher).toHaveBeenCalledWith(
      "/api/v1/auth/register",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ identifier: "new@example.com", password: "password1" }) }),
    );
    expect(store.token).toBe("reg-token");
    fetcher.mockRestore();
  });
});

