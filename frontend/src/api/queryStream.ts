export type SSEEvent = { type: string; data: unknown };

export async function parseSSEStream(response: Response, onEvent: (event: SSEEvent) => void): Promise<void> {
  if (!response.ok || !response.body) throw new Error(`SSE request failed: ${response.status}`);
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ""; let eventType = "message"; let dataLines: string[] = [];
  const dispatch = () => { if (!dataLines.length) return; const raw = dataLines.join("\n"); let data: unknown = raw; try { data = JSON.parse(raw); } catch {} onEvent({ type: eventType, data }); eventType = "message"; dataLines = []; };
  while (true) { const { value, done } = await reader.read(); buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done }); const lines = buffer.split(/\r?\n/); buffer = lines.pop() ?? ""; for (const line of lines) { if (!line) { dispatch(); continue; } if (line.startsWith("event:")) eventType = line.slice(6).trim(); else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart()); } if (done) { if (buffer.startsWith("data:")) dataLines.push(buffer.slice(5).trimStart()); dispatch(); break; } }
}
