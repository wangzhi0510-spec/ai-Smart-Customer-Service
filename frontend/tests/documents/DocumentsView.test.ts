import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import DocumentsView from "../../src/views/DocumentsView.vue";

const documentsStore = {
  documents: [
    { id: "d1", original_name: "退款政策.md", status: "ready", size_bytes: 1024, chunk_count: 4 },
    { id: "d2", original_name: "失败文档.pdf", status: "failed", error_code: "PDF_PARSE_FAILED", size_bytes: 2048, chunk_count: 0 },
  ],
  loading: false,
  error: null,
  list: vi.fn().mockResolvedValue([]),
  upload: vi.fn().mockResolvedValue({ id: "d3", original_name: "新文档.txt", status: "pending" }),
  remove: vi.fn().mockResolvedValue(undefined),
};

vi.mock("../../src/stores/documents", () => ({ useDocumentsStore: () => documentsStore }));

describe("DocumentsView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    documentsStore.documents = [
      { id: "d1", original_name: "退款政策.md", status: "ready", size_bytes: 1024, chunk_count: 4 },
      { id: "d2", original_name: "失败文档.pdf", status: "failed", error_code: "PDF_PARSE_FAILED", size_bytes: 2048, chunk_count: 0 },
    ];
    vi.stubGlobal("confirm", vi.fn(() => true));
  });

  it("loads documents, shows statuses and failure reason, and deletes after confirmation", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div />" } }, { path: "/chat", component: { template: "<div />" } }] });
    const wrapper = mount(DocumentsView, { global: { plugins: [router] } });
    await Promise.resolve();
    expect(documentsStore.list).toHaveBeenCalled();
    expect(wrapper.text()).toContain("退款政策.md");
    expect(wrapper.text()).toContain("已就绪");
    expect(wrapper.text()).toContain("PDF_PARSE_FAILED");
    await wrapper.get("button[data-document-id='d1']").trigger("click");
    expect(documentsStore.remove).toHaveBeenCalledWith("d1");
  });

  it("rejects unsupported extensions before upload", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/", component: { template: "<div />" } }, { path: "/chat", component: { template: "<div />" } }] });
    const wrapper = mount(DocumentsView, { global: { plugins: [router] } });
    const file = new File(["binary"], "malware.exe", { type: "application/octet-stream" });
    const input = wrapper.get("input[type='file']");
    Object.defineProperty(input.element, "files", { configurable: true, value: [file] });
    input.element.dispatchEvent(new Event("change", { bubbles: true }));
    await nextTick();
    expect(documentsStore.upload).not.toHaveBeenCalled();
    expect(wrapper.get("[role='alert']").text()).toContain("仅支持 TXT、MD 和 PDF");
  });
});
