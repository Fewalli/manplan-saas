from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserListItem

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserListItem])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "coordenador_manutencao")),
) -> list[UserListItem]:
    stmt = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.tenant_id == current_user.tenant_id)
        .order_by(User.full_name.asc())
    )
    users = db.execute(stmt).scalars().all()
    return [
        UserListItem(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            roles=[user_role.role.code for user_role in user.user_roles if user_role.role],
        )
        for user in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserListItem)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant")),
) -> UserListItem:
    role_stmt = select(Role).where(
        Role.tenant_id == current_user.tenant_id,
        Role.code.in_(payload.role_codes),
        Role.is_active.is_(True),
    )
    roles = db.execute(role_stmt).scalars().all()

    user = User(
        tenant_id=current_user.tenant_id,
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    for role in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    db.commit()

    stmt = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user.id)
    )
    created_user = db.execute(stmt).scalar_one()

    return UserListItem(
        id=created_user.id,
        full_name=created_user.full_name,
        email=created_user.email,
        is_active=created_user.is_active,
        roles=[user_role.role.code for user_role in created_user.user_roles if user_role.role],
    )