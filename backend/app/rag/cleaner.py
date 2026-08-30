from __future__ import annotations

import re

from .parsers.base import ParsedPage


def clean_pages(pages: list[ParsedPage]) -> list[ParsedPage]:
    cleaned: list[ParsedPage] = []
    for page in pages:
        lines: list[str] = []
        in_code = False
        for raw_line in page.text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                lines.append(stripped)
                continue
            if in_code:
                lines.append(raw_line.rstrip())
            elif stripped:
                lines.append(re.sub(r"[ \t]+", " ", stripped))
        text = "\n".join(lines).strip()
        if text:
            cleaned.append(
                ParsedPage(
                    text=text,
                    page_number=page.page_number,
                    source_name=page.source_name,
                    section_title=page.section_title,
                )
            )
    return cleaned

