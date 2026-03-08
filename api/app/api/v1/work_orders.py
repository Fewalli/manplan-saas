from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.work_order import (
    ExecutionNowRead,
    WorkOrderClose,
    WorkOrderCreate,
    WorkOrderFinalize,
    WorkOrderRead,
    WorkOrderSuspend,
)
from app.services.work_orders import (
    DomainError,
    close_work_order,
    create_work_order,
    finalize_work_order,
    get_execution_now,
    get_work_order_or_404,
    list_work_orders,
    start_work_order,
    suspend_work_order,
)

router = APIRouter(prefix="/work-orders", tags=["work-orders"])


def _raise_domain(exc: DomainError):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order_endpoint(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return create_work_order(db, current_user=current_user, payload=payload)
    except DomainError as exc:
        _raise_domain(exc)


@router.get("", response_model=list[WorkOrderRead])
def list_work_orders_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_work_orders(db, tenant_id=current_user.tenant_id)


@router.get("/{work_order_id}", response_model=WorkOrderRead)
def get_work_order_endpoint(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return get_work_order_or_404(db, tenant_id=current_user.tenant_id, work_order_id=work_order_id)
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{work_order_id}/start", response_model=WorkOrderRead)
def start_work_order_endpoint(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return start_work_order(db, current_user=current_user, work_order_id=work_order_id)
    except DomainError as exc:
        _raise_domain(exc)


@router.post("/{work_order_id}/resume", response_model=WorkOrderRead)
def resume_work_order_endpoint(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return start_work_order(db, current_user=current_user, work_order_id=work_order_id)
    except DomainError as exc:
        _raise_domain(exc)


@router.post("/{work_order_id}/suspend", response_model=WorkOrderRead)
def suspend_work_order_endpoint(
    work_order_id: int,
    payload: WorkOrderSuspend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return suspend_work_order(db, current_user=current_user, work_order_id=work_order_id, payload=payload)
    except DomainError as exc:
        _raise_domain(exc)


@router.post("/{work_order_id}/finalize", response_model=WorkOrderRead)
def finalize_work_order_endpoint(
    work_order_id: int,
    payload: WorkOrderFinalize,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return finalize_work_order(db, current_user=current_user, work_order_id=work_order_id, payload=payload)
    except DomainError as exc:
        _raise_domain(exc)


@router.post("/{work_order_id}/close", response_model=WorkOrderRead)
def close_work_order_endpoint(
    work_order_id: int,
    payload: WorkOrderClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return close_work_order(db, current_user=current_user, work_order_id=work_order_id, payload=payload)
    except DomainError as exc:
        _raise_domain(exc)


@router.get("/monitor/execution-now", response_model=list[ExecutionNowRead])
def execution_now_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rows = get_execution_now(db, tenant_id=current_user.tenant_id)
    return [
        ExecutionNowRead(
            technician_id=row.technician_id,
            work_order_id=row.work_order_id,
            work_order_code=row.work_order_code,
            asset_id=row.asset_id,
            started_at=row.started_at,
            elapsed_minutes=max(0, int((row.elapsed_seconds or 0) // 60)),
        )
        for row in rows
    ]