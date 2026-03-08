from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.rbac import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User

DEFAULT_ROLES = [
    ("solicitante", "Solicitante"),
    ("tecnico", "Técnico"),
    ("planejador", "Planejador"),
    ("coordenador_manutencao", "Coordenador de Manutenção"),
    ("administrativo", "Administrativo"),
    ("admin_tenant", "Admin do Tenant"),
]


def run() -> None:
    db: Session = SessionLocal()
    try:
        tenant = db.execute(
            select(Tenant).where(Tenant.slug == settings.INITIAL_TENANT_SLUG)
        ).scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                name=settings.INITIAL_TENANT_NAME,
                slug=settings.INITIAL_TENANT_SLUG,
                is_active=True,
            )
            db.add(tenant)
            db.flush()

        existing_roles = {
            r.code: r
            for r in db.execute(select(Role).where(Role.tenant_id == tenant.id)).scalars().all()
        }

        for code, name in DEFAULT_ROLES:
            if code not in existing_roles:
                db.add(Role(tenant_id=tenant.id, code=code, name=name, is_active=True))

        db.flush()

        admin = db.execute(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == settings.INITIAL_ADMIN_EMAIL.lower(),
            )
        ).scalar_one_or_none()

        if not admin:
            admin = User(
                tenant_id=tenant.id,
                full_name=settings.INITIAL_ADMIN_NAME,
                email=settings.INITIAL_ADMIN_EMAIL.lower(),
                password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                is_active=True,
            )
            db.add(admin)
            db.flush()

        admin_role = db.execute(
            select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin_tenant")
        ).scalar_one()

        already_linked = db.execute(
            select(UserRole).where(UserRole.user_id == admin.id, UserRole.role_id == admin_role.id)
        ).scalar_one_or_none()

        if not already_linked:
            db.add(UserRole(user_id=admin.id, role_id=admin_role.id))

        db.commit()
        print("Seed inicial concluído com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    run()