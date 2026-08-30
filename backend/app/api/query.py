from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.sse import serialize_event
from backend.app.core.config import Settings
from backend.app.core.errors import AppError, error_envelope
from backend.app.core.security import get_current_user
from backend.app.db.session import get_session
from backend.app.models.chat_session import ChatSession
from backend.app.models.message import Message, MessageSource
from backend.app.models.user import User
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.services.qa_service import QAService
from backend.app.services.session_service import SessionService
from backend.app.services.usage_service import UsageService

router = APIRouter(prefix="/api/v1/query", tags=["query"])


def get_qa(request: Request) -> QAService:
    qa = getattr(request.app.state, "qa_service", None)
    if qa is None:
        raise AppError("QA_UNAVAILABLE", "问答服务暂时不可用", 503)
    return qa


def get_usage(db: Session = Depends(get_session)) -> UsageService:
    return UsageService(db, daily_limit=Settings.from_env().daily_question_limit)


def _session(db: Session, user: User, session_id: str) -> ChatSession:
    return SessionService(db).get(user.id, session_id)


def _persist(db: Session, request: QueryRequest, result, answer: str, status: str = "completed", assistant_id: str | None = None) -> str:
    user_message = Message(id=str(uuid4()), session_id=request.session_id, role="user", content=request.question, status="completed")
    assistant_id = assistant_id or str(uuid4())
    assistant = Message(id=assistant_id, session_id=request.session_id, role="assistant", content=answer,
                        answer_type=result.answer_type, retrieval_strategy=result.retrieval_strategy,
                        latency_ms=result.latency_ms, status=status)
    db.add_all([user_message, assistant])
    for order, source in enumerate(result.sources, start=1):
        db.add(MessageSource(id=str(uuid4()), message_id=assistant_id, document_id=str(source.get("document_id", "")),
                             document_name=source.get("document_name", ""), page_number=source.get("page_number"),
                             section_title=source.get("section_title"), excerpt=source.get("excerpt", ""),
                             retrieval_score=source.get("retrieval_score"), display_order=order))
    db.commit()
    return assistant_id


@router.post("", response_model=QueryResponse)
def query(payload: QueryRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session), usage: UsageService = Depends(get_usage)):
    qa = get_qa(request)
    _session(db, user, payload.session_id)
    reservation = usage.reserve(user.id)
    try:
        result = qa.answer(payload.question, payload.session_id, user.id)
        message_id = _persist(db, payload, result, result.answer)
        return QueryResponse(message_id=message_id, answer=result.answer, answer_type=result.answer_type,
                             retrieval_strategy=result.retrieval_strategy, sources=result.sources,
                             latency_ms=result.latency_ms, warnings=result.warnings)
    except Exception:
        usage.compensate(reservation)
        raise


@router.post("/stream")
async def query_stream(payload: QueryRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_session), usage: UsageService = Depends(get_usage)):
    qa = get_qa(request)
    _session(db, user, payload.session_id)
    reservation = usage.reserve(user.id)
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    async def events():
        started = perf_counter()
        assistant_id = str(uuid4())
        try:
            result = qa.answer(payload.question, payload.session_id, user.id)
            yield serialize_event("start", {"request_id": request_id, "message_id": assistant_id})
            chunks = qa.stream(payload.question, payload.session_id, user.id) if hasattr(qa, "stream") and result.answer_type == "rag" else _single(result.answer)
            answer_parts: list[str] = []
            async for chunk in _as_async(chunks):
                answer_parts.append(str(chunk))
                yield serialize_event("delta", {"text": chunk})
            for source in result.sources:
                yield serialize_event("source", source)
            _persist(db, payload, result, "".join(answer_parts), assistant_id=assistant_id)
            yield serialize_event("done", {"message_id": assistant_id, "answer_type": result.answer_type,
                                            "retrieval_strategy": result.retrieval_strategy, "latency_ms": max(0, int((perf_counter() - started) * 1000))})
        except AppError as exc:
            usage.compensate(reservation)
            yield serialize_event("error", error_envelope(exc, request_id)["error"])
        except Exception:
            usage.compensate(reservation)
            yield serialize_event("error", {"code": "QA_FAILED", "message": "问答服务暂时不可用", "details": {}, "request_id": request_id})

    return StreamingResponse(events(), media_type="text/event-stream")


async def _as_async(value):
    if hasattr(value, "__aiter__"):
        async for item in value:
            yield item
    else:
        for item in value:
            yield item


def _single(value):
    async def generator():
        yield value

    return generator()





