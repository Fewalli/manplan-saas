from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.area import Area
from app.models.user import User
from app.schemas.area import AreaCreate, AreaRead

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("", response_model=list[AreaRead])
def list_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "planejador", "coordenador_manutencao")),
):
    stmt = (
        select(Area)
        .where(Area.tenant_id == current_user.tenant_id)
        .order_by(Area.name.asc())
    )
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
def create_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "planejador")),
):
    area = Area(
        tenant_id=current_user.tenant_id,
        code=payload.code,
        name=payload.name,
        is_active=True,
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area