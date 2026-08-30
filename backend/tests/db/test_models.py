from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.chat_session import ChatSession
from backend.app.models.message import Message, MessageSource
from backend.app.models.document import Document
from backend.app.models.usage import UsageRecord

def test_sqlite_persists_domain_graph_and_enforces_constraints():
    engine=create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    assert {"users","chat_sessions","messages","message_sources","message_feedback","documents","fqa_entries","usage_records"} <= set(Base.metadata.tables)
    uid=str(uuid4()); did=str(uuid4())
    with Session(engine) as db:
        user=User(id=uid,email="a@example.com",password_hash="hash")
        doc=Document(id=did,user_id=uid,original_name="faq.md",storage_path="x",media_type="text/markdown",size_bytes=1,content_sha256="a"*64)
        chat=ChatSession(id=str(uuid4()),user_id=uid,title="help")
        msg=Message(id=str(uuid4()),session_id=chat.id,role="assistant",content="answer",answer_type="rag",status="completed")
        msg.sources.append(MessageSource(id=str(uuid4()),message_id=msg.id,document_id=did,document_name="faq.md",excerpt="answer",display_order=1))
        usage=UsageRecord(id=str(uuid4()),user_id=uid,usage_date=datetime.now(timezone.utc).date(),question_count=1)
        db.add_all([user,doc,chat,msg,usage]); db.commit()
        assert db.scalar(select(Message).where(Message.id==msg.id)).sources[0].document_name=="faq.md"
        db.add(User(id=str(uuid4()),email="a@example.com",password_hash="other"))
        try: db.commit(); assert False
        except IntegrityError: db.rollback()




