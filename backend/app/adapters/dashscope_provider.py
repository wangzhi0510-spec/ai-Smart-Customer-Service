from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import httpx

from backend.app.core.config import Settings
from backend.app.core.errors import AppError


class DashScopeProvider:
    def __init__(self, settings: Settings | None = None, client: Any | None = None):
        settings = settings or Settings.from_env()
        self.api_key = settings.dashscope_api_key
        self.base_url = settings.dashscope_base_url.rstrip("/")
        self.model = settings.llm_model
        self.client = client

    def complete(self, messages: list) -> str:
        if not self.api_key:
            raise AppError("LLM_UNAVAILABLE", "LLM 服务未配置", 503)
        payload = {"model": self.model, "messages": [self._message(item) for item in messages], "stream": False}
        try:
            response = (self.client or httpx.Client(timeout=30)).post(
                f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            raise AppError("LLM_FAILED", "LLM 服务暂时不可用", 503) from exc

    async def stream(self, messages: list) -> AsyncIterator[str]:
        if not self.api_key:
            raise AppError("LLM_UNAVAILABLE", "LLM 服务未配置", 503)
        payload = {"model": self.model, "messages": [self._message(item) for item in messages], "stream": True}
        client = self.client or httpx.AsyncClient(timeout=30)
        try:
            async with client.stream("POST", f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line[6:] != "[DONE]":
                        data = httpx.Response(200, content=line[6:]).json()
                        delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            yield delta
        except AppError:
            raise
        except Exception as exc:
            raise AppError("LLM_FAILED", "LLM 服务暂时不可用", 503) from exc
        finally:
            if self.client is None:
                await client.aclose()

    @staticmethod
    def _message(item: Any) -> dict[str, str]:
        if isinstance(item, dict):
            return {"role": str(item.get("role", "user")), "content": str(item.get("content", ""))}
        return {"role": str(getattr(item, "role", "user")), "content": str(getattr(item, "content", ""))}

