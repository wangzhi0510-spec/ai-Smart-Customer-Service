export type HttpClientOptions = { fetcher?: typeof fetch; getToken?: () => string | null; onUnauthorized?: () => void };

export function createHttpClient(options: HttpClientOptions = {}) {
  const fetcher = options.fetcher ?? fetch;
  return {
    async request<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
      const headers = new Headers(init.headers);
      if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
      const token = options.getToken?.(); if (token) headers.set("Authorization", `Bearer ${token}`);
      const response = await fetcher(path, { ...init, headers });
      if (response.status === 401) { options.onUnauthorized?.(); throw new Error("UNAUTHORIZED"); }
      if (!response.ok) { const body = await response.json().catch(() => ({})); throw Object.assign(new Error(body?.error?.message ?? "请求失败"), { code: body?.error?.code, status: response.status }); }
      if (response.status === 204) return undefined as T;
      return response.json() as Promise<T>;
    },
  };
}
