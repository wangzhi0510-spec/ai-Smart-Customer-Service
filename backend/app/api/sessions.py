from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.db.session import get_session
from backend.app.models.user import User
from backend.app.schemas.session import (
    FeedbackRead,
    FeedbackUpdate,
    MessageRead,
    SessionCreate,
    SessionRead,
    SessionUpdate,
)
from backend.app.services.session_service import SessionService

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.post("/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).create(user.id, payload.title)


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).list(user.id, page, page_size)


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session_detail(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).get(user.id, session_id)


@router.put("/sessions/{session_id}", response_model=SessionRead)
def update_session(
    session_id: str,
    payload: SessionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).update(user.id, session_id, payload.title)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    SessionService(db).delete(user.id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
def list_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).messages(user.id, session_id)


@router.put("/messages/{message_id}/feedback", response_model=FeedbackRead)
def update_feedback(
    message_id: str,
    payload: FeedbackUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return SessionService(db).feedback(user.id, message_id, payload.rating, payload.comment)
