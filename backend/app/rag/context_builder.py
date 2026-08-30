from __future__ import annotations

from .prompts import build_rag_messages


def build_context(contexts: list, token_budget: int) -> str:
    max_chars = max(0, token_budget * 4)
    parts: list[str] = []
    used = 0
    for index, item in enumerate(contexts, start=1):
        marker = f"[{index}] 文档ID={item.document_id or 'unknown'} 来源={item.source_name} 第 {item.page_number or '-'} 页"
        if item.section_title:
            marker += f" 章节={item.section_title}"
        block = f"{marker}\n{item.text}"
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining].rstrip()
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


__all__ = ["build_context", "build_rag_messages"]
