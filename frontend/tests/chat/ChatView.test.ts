import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import ChatView from "../../src/views/ChatView.vue";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";

const chat = {
  sessions: [{ id: "s1", title: "售后咨询" }],
  messages: [{ id: "m1", session_id: "s1", role: "assistant", content: "请提供订单号", status: "completed", sources: [] }],
  streaming: false,
  error: null,
  listSessions: vi.fn().mockImplementation(() => Promise.resolve(chat.sessions)),
  createSession: vi.fn().mockResolvedValue({ id: "s2", title: "新会话" }),
  updateSession: vi.fn().mockImplementation(async (id: string, title: string) => ({ id, title })),
  loadMessages: vi.fn().mockResolvedValue([]),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  streamQuestion: vi.fn().mockImplementation(async (_id: string, _question: string, onEvent: (event: any) => void) => {
    onEvent({ type: "start", data: { message_id: "m2" } });
    onEvent({ type: "delta", data: { text: "可以办理。" } });
    onEvent({ type: "source", data: { id: "src1", document_name: "退款政策.md", excerpt: "七日内可申请退款" } });
    onEvent({ type: "done", data: { message_id: "m2" } });
  }),
  submitFeedback: vi.fn().mockResolvedValue(undefined),
};

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div />" } }, { path: "/login", component: { template: "<div />" } }, { path: "/documents", component: { template: "<div />" } }] });

vi.mock("../../src/stores/chat", () => ({ useChatStore: () => chat }));

describe("ChatView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    chat.sessions = [{ id: "s1", title: "售后咨询" }];
    chat.messages = [{ id: "m1", session_id: "s1", role: "assistant", content: "请提供订单号", status: "completed", sources: [] }];
    chat.listSessions.mockImplementation(() => Promise.resolve(chat.sessions));
    chat.streaming = false;
    chat.error = null;
  });

  it("renders session sidebar and streams delta/source with feedback", async () => {
    const wrapper = mount(ChatView, { global: { plugins: [router] } });
    await vi.waitFor(() => expect(wrapper.get("[data-testid='session-sidebar']").text()).toContain("售后咨询"));
    await wrapper.get("textarea").setValue("我想退款");
    await wrapper.get("form").trigger("submit");
    expect(chat.streamQuestion).toHaveBeenCalledWith("s1", "我想退款", expect.any(Function));
    expect(wrapper.text()).toContain("可以办理。");
    expect(wrapper.text()).toContain("退款政策.md");
    await wrapper.get("button[aria-label='赞同回答']").trigger("click");
    expect(chat.submitFeedback).toHaveBeenCalledWith("m2", "positive");
  });

  it("creates, switches, deletes sessions and exposes retry on errors", async () => {
    const wrapper = mount(ChatView, { global: { plugins: [router] } });
    await vi.waitFor(() => expect(wrapper.get("button[aria-label='新建会话']")).toBeTruthy());
    await wrapper.get("button[aria-label='新建会话']").trigger("click");
    expect(chat.createSession).toHaveBeenCalled();
    await wrapper.get("button[data-session-id='s1']").trigger("click");
    expect(chat.loadMessages).toHaveBeenCalledWith("s1");
    await wrapper.get("button[aria-label='删除会话']").trigger("click");
    expect(chat.deleteSession).toHaveBeenCalledWith("s1");
  });

  it("auto-creates a session when the account has no sessions and allows renaming", async () => {
    chat.sessions = [];
    chat.listSessions.mockResolvedValueOnce([]);
    chat.createSession.mockResolvedValueOnce({ id: "s-new", title: "新会话" });
    const wrapper = mount(ChatView, { global: { plugins: [router] } });
    await vi.waitFor(() => expect(chat.createSession).toHaveBeenCalledWith("新会话"));
    expect(wrapper.get("[data-session-id='s-new']").exists()).toBe(true);
    await wrapper.get("button[aria-label='重命名会话']").trigger("click");
    const input = wrapper.get("input[aria-label='会话名称']");
    await input.setValue("订单售后");
    await input.trigger("keydown.enter");
    await vi.waitFor(() => expect(chat.updateSession).toHaveBeenCalledWith("s-new", "订单售后"));
  });
});
