from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: str
    original_name: str
    media_type: str
    size_bytes: int
    content_sha256: str
    status: str
    version: int
    chunk_count: int
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

