from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import AppError
from backend.app.models.chat_session import ChatSession
from backend.app.models.feedback import MessageFeedback
from backend.app.models.message import Message


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, title: str) -> ChatSession:
        item = ChatSession(id=str(uuid4()), user_id=user_id, title=title.strip() or "新会话")
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list(self, user_id: str) -> list[ChatSession]:
        query = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.is_deleted.is_(False))
            .order_by(ChatSession.updated_at.desc())
        )
        return list(self.db.scalars(query).all())

    def get(self, user_id: str, session_id: str) -> ChatSession:
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.is_deleted.is_(False),
        )
        item = self.db.scalar(query)
        if item is None:
            raise AppError("NOT_FOUND", "会话不存在", 404)
        return item

    def delete(self, user_id: str, session_id: str) -> None:
        item = self.db.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        if item is None:
            raise AppError("NOT_FOUND", "会话不存在", 404)
        if not item.is_deleted:
            item.is_deleted = True
            self.db.commit()

    def messages(self, user_id: str, session_id: str) -> list[Message]:
        self.get(user_id, session_id)
        query = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        return list(self.db.scalars(query).unique().all())

    def feedback(
        self, user_id: str, message_id: str, rating: str, comment: str | None
    ) -> MessageFeedback:
        query = (
            select(Message)
            .join(ChatSession, Message.session_id == ChatSession.id)
            .where(
                Message.id == message_id,
                Message.role == "assistant",
                ChatSession.user_id == user_id,
                ChatSession.is_deleted.is_(False),
            )
        )
        if self.db.scalar(query) is None:
            raise AppError("NOT_FOUND", "消息不存在或无权反馈", 404)

        item = self.db.scalar(
            select(MessageFeedback).where(
                MessageFeedback.message_id == message_id,
                MessageFeedback.user_id == user_id,
            )
        )
        if item is None:
            item = MessageFeedback(
                id=str(uuid4()),
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
            )
            self.db.add(item)
        else:
            item.rating = rating
            item.comment = comment
        self.db.commit()
        self.db.refresh(item)
        return item
