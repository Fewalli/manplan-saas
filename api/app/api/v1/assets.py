from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.area import Area
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetRead

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetRead])
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "planejador", "coordenador_manutencao", "tecnico")),
):
    stmt = (
        select(
            Asset.id,
            Asset.area_id,
            Area.code.label("area_code"),
            Area.name.label("area_name"),
            Asset.code,
            Asset.name,
            Asset.location,
            Asset.is_active,
        )
        .join(Area, Area.id == Asset.area_id)
        .where(Asset.tenant_id == current_user.tenant_id)
        .order_by(Asset.name.asc())
    )

    rows = db.execute(stmt).mappings().all()
    return [AssetRead(**row) for row in rows]


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_tenant", "planejador")),
):
    area = db.execute(
        select(Area).where(
            Area.id == payload.area_id,
            Area.tenant_id == current_user.tenant_id,
            Area.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Área inválida para este tenant.",
        )

    asset = Asset(
        tenant_id=current_user.tenant_id,
        area_id=payload.area_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        location=payload.location.strip() if payload.location else None,
        is_active=True,
    )
    db.add(asset)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um ativo com este código neste tenant.",
        )

    stmt = (
        select(
            Asset.id,
            Asset.area_id,
            Area.code.label("area_code"),
            Area.name.label("area_name"),
            Asset.code,
            Asset.name,
            Asset.location,
            Asset.is_active,
        )
        .join(Area, Area.id == Asset.area_id)
        .where(Asset.id == asset.id)
    )
    row = db.execute(stmt).mappings().one()
    return AssetRead(**row)