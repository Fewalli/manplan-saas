from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.security import create_access_token, create_password_reset_safe_message
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user
from app.models.role import Role, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_password_reset_safe_message(),
        )

    token = create_access_token(subject=user.email, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_active_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        full_name=current_user.full_name,
        email=current_user.email,
        roles=[ur.role.code for ur in current_user.user_roles if ur.role],
    )