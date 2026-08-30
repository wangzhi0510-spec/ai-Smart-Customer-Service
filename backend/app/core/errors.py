from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, Any] | None = None
    def __post_init__(self): super().__init__(self.message)
def error_envelope(error: AppError, request_id: str) -> dict[str, Any]:
    return {"error":{"code":error.code,"message":error.message,"details":error.details or {},"request_id":request_id}}
def sse_error_event(error: AppError, request_id: str) -> str:
    return f"event: error\ndata: {json.dumps(error_envelope(error, request_id)['error'], ensure_ascii=False)}\n\n"
