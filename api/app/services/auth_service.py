from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import verify_password
from app.models.role import UserRole
from app.models.user import User
from app.models.role import UserRole


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    stmt = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.email == str(email).lower())
    )
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user