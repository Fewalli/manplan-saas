from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/tenant", tags=["tenant"])


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool


@router.get("/me", response_model=TenantResponse)
def read_current_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "coordenador_manutencao")),
) -> TenantResponse:
    tenant = db.get(Tenant, current_user.tenant_id)
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
    )