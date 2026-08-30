from __future__ import annotations

from typing import Any

from redis import Redis

from backend.app.core.config import Settings


class RedisClient:
    """Small infrastructure adapter so services can be tested with a fake Redis."""

    def __init__(self, client: Any | None = None, settings: Settings | None = None):
        self._client = client or Redis.from_url((settings or Settings.from_env()).redis_url, decode_responses=True)

    def get(self, key: str) -> str | bytes | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> Any:
        return self._client.set(key, value, ex=ex)

    def setex(self, key: str, seconds: int, value: str) -> Any:
        return self._client.setex(key, seconds, value)

    def incr(self, key: str) -> int:
        return int(self._client.incr(key))

    def decr(self, key: str) -> int:
        return int(self._client.decr(key))

    def expire(self, key: str, seconds: int) -> bool:
        return bool(self._client.expire(key, seconds))
