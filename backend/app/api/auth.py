from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.core.config import Settings
from backend.app.core.security import get_current_user,create_access_token
from backend.app.db.session import get_session
from backend.app.models.user import User
from backend.app.schemas.auth import AuthRequest,PublicUser,TokenResponse
from backend.app.services.auth_service import AuthService
router=APIRouter(prefix="/api/v1/auth",tags=["auth"])
@router.post("/register",response_model=TokenResponse,status_code=status.HTTP_201_CREATED)
def register(payload: AuthRequest, db: Session=Depends(get_session), settings: Settings=Depends(Settings.from_env)):
    user=AuthService(db,settings).register(payload.identifier,payload.password)
    return TokenResponse(access_token=create_access_token(user.id,settings),user=PublicUser.model_validate(user,from_attributes=True))
@router.post("/login",response_model=TokenResponse)
def login(payload: AuthRequest, db: Session=Depends(get_session), settings: Settings=Depends(Settings.from_env)):
    return AuthService(db,settings).authenticate(payload.identifier,payload.password)
@router.get("/me",response_model=PublicUser)
def me(user: User=Depends(get_current_user)): return PublicUser.model_validate(user,from_attributes=True)
