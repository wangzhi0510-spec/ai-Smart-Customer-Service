from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    question: str = Field(min_length=1, max_length=500)


class QueryResponse(BaseModel):
    message_id: str
    answer: str
    answer_type: str
    retrieval_strategy: str | None = None
    sources: list[dict] = Field(default_factory=list)
    latency_ms: int = 0
    warnings: list[str] = Field(default_factory=list)
