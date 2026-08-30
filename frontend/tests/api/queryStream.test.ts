import { describe, expect, it, vi } from "vitest";
import { parseSSEStream } from "../../src/api/queryStream";
import { createHttpClient } from "../../src/api/http";

describe("query stream protocol", () => {
  it("parses multiline data and preserves event order", async () => {
    const events: Array<{ type: string; data: unknown }> = [];
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode("event: start\ndata: {\"id\":\"m1\"}\n\nevent: delta\ndata: {\"text\":\ndata: \"hello\"}\n\n"));
        controller.close();
      },
    });

    await parseSSEStream(new Response(body), (event) => events.push(event));

    expect(events).toEqual([
      { type: "start", data: { id: "m1" } },
      { type: "delta", data: { text: "hello" } },
    ]);
  });

  it("adds bearer token to JSON requests and clears it on unauthorized", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    const client = createHttpClient({ fetcher, getToken: () => "token-1", onUnauthorized: vi.fn() });

    await client.request("/api/v1/sessions");

    expect(fetcher.mock.calls[0][1].headers.get("Authorization")).toBe("Bearer token-1");
  });
});




