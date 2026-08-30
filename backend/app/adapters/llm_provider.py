from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, messages: list) -> str: ...

    def stream(self, messages: list) -> AsyncIterator[str]: ...

