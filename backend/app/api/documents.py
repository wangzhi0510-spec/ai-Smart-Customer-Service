from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.security import get_current_user
from backend.app.db.session import get_session
from backend.app.models.user import User
from backend.app.schemas.document import DocumentRead
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def service(db: Session = Depends(get_session), settings: Settings = Depends(Settings.from_env)) -> DocumentService:
    return DocumentService(db, settings)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
def upload_document(file: UploadFile = File(...), user: User = Depends(get_current_user), documents: DocumentService = Depends(service)):
    return documents.create(user.id, file.file, file.filename or "", file.content_type or "")


@router.get("", response_model=list[DocumentRead])
def list_documents(user: User = Depends(get_current_user), documents: DocumentService = Depends(service)):
    return documents.list(user.id)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, user: User = Depends(get_current_user), documents: DocumentService = Depends(service)):
    return documents.get(user.id, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, user: User = Depends(get_current_user), documents: DocumentService = Depends(service)):
    documents.delete(user.id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
