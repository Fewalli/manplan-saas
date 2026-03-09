from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.rbac import user_has_any_role
from app.models.area import Area
from app.models.asset import Asset
from app.models.execution_session import ExecutionSession
from app.models.role import UserRole
from app.models.user import User
from app.models.work_order import WorkOrder, WorkOrderStatus, WorkOrderType
from app.models.work_order_counter import WorkOrderCounter
from app.models.work_order_event import WorkOrderEvent, WorkOrderEventType
from app.schemas.work_order import WorkOrderClose, WorkOrderCreate, WorkOrderFinalize, WorkOrderSuspend


class DomainError(Exception):
    pass


BLOCK_MESSAGE = (
    "Você já está em execução na OS {code}. Para iniciar outra, suspenda a OS atual "
    "(com motivo e descrição)."
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_code(order_type: WorkOrderType, sequence_number: int, revision_number: int = 0) -> str:
    base = f"{order_type.value}{sequence_number:04d}"
    return f"{base}-R{revision_number}" if revision_number >= 1 else base


def next_sequence_number(db: Session, tenant_id: int) -> int:
    counter = db.execute(
        select(WorkOrderCounter).where(WorkOrderCounter.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if counter is None:
        counter = WorkOrderCounter(tenant_id=tenant_id, current_value=0)
        db.add(counter)
        db.flush()

    counter.current_value += 1
    db.flush()
    return counter.current_value


def add_event(
    db: Session,
    *,
    work_order_id: int,
    actor_user_id: int,
    event_type: WorkOrderEventType,
    description: str | None = None,
    payload: dict | None = None,
) -> None:
    db.add(
        WorkOrderEvent(
            work_order_id=work_order_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            description=description,
            payload=payload,
        )
    )


def _with_roles_stmt(user_id: int):
    return (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )


def _serialize_work_order_row(row) -> dict:
    return {
        "id": row.id,
        "code": row.code,
        "type": row.type,
        "status": row.status,
        "requester_id": row.requester_id,
        "asset_id": row.asset_id,
        "asset_code": row.asset_code,
        "asset_name": row.asset_name,
        "asset_location": row.asset_location,
        "area_id": row.area_id,
        "area_code": row.area_code,
        "area_name": row.area_name,
        "description": row.description,
        "scheduled_date": row.scheduled_date,
        "technician_current_id": row.technician_current_id,
        "machine_stopped": row.machine_stopped,
        "technician_downtime_minutes": row.technician_downtime_minutes,
        "requester_downtime_minutes": row.requester_downtime_minutes,
        "met_expectation": row.met_expectation,
        "finalization_at": row.finalization_at,
        "closure_at": row.closure_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _enriched_work_order_stmt(*, tenant_id: int):
    return (
        select(
            WorkOrder.id,
            WorkOrder.code,
            WorkOrder.type,
            WorkOrder.status,
            WorkOrder.requester_id,
            WorkOrder.asset_id,
            Asset.code.label("asset_code"),
            Asset.name.label("asset_name"),
            Asset.location.label("asset_location"),
            Area.id.label("area_id"),
            Area.code.label("area_code"),
            Area.name.label("area_name"),
            WorkOrder.description,
            WorkOrder.scheduled_date,
            WorkOrder.technician_current_id,
            WorkOrder.machine_stopped,
            WorkOrder.technician_downtime_minutes,
            WorkOrder.requester_downtime_minutes,
            WorkOrder.met_expectation,
            WorkOrder.finalization_at,
            WorkOrder.closure_at,
            WorkOrder.created_at,
            WorkOrder.updated_at,
        )
        .select_from(WorkOrder)
        .outerjoin(Asset, Asset.id == WorkOrder.asset_id)
        .outerjoin(Area, Area.id == Asset.area_id)
        .where(WorkOrder.tenant_id == tenant_id)
    )


def _get_valid_asset_or_raise(db: Session, *, tenant_id: int, asset_id: int) -> Asset:
    asset = db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()

    if asset is None:
        raise DomainError("Ativo inválido para este tenant")
    if not asset.is_active:
        raise DomainError("Ativo inativo não pode receber nova OS")
    if asset.area_id is None:
        raise DomainError("Ativo sem área vinculada não pode receber nova OS")

    return asset


def create_work_order(db: Session, *, current_user: User, payload: WorkOrderCreate) -> WorkOrder:
    asset = _get_valid_asset_or_raise(
        db,
        tenant_id=current_user.tenant_id,
        asset_id=payload.asset_id,
    )

    machine_stopped = payload.type == WorkOrderType.OSC
    sequence_number = next_sequence_number(db, current_user.tenant_id)
    code = make_code(payload.type, sequence_number)

    wo = WorkOrder(
        tenant_id=current_user.tenant_id,
        type=payload.type,
        status=WorkOrderStatus.ABERTA,
        sequence_number=sequence_number,
        revision_number=0,
        code=code,
        requester_id=current_user.id,
        asset_id=asset.id,
        description=payload.description,
        scheduled_date=payload.scheduled_date,
        machine_stopped=machine_stopped,
    )
    db.add(wo)
    db.flush()

    add_event(
        db,
        work_order_id=wo.id,
        actor_user_id=current_user.id,
        event_type=WorkOrderEventType.OPENED,
        payload={
            "type": payload.type.value,
            "description": payload.description,
            "asset_id": asset.id,
        },
    )

    db.commit()
    db.refresh(wo)
    return wo


def list_work_orders(db: Session, *, tenant_id: int) -> list[dict]:
    stmt = (
        _enriched_work_order_stmt(tenant_id=tenant_id)
        .order_by(WorkOrder.created_at.desc(), WorkOrder.id.desc())
    )
    rows = db.execute(stmt).mappings().all()
    return [_serialize_work_order_row(row) for row in rows]


def get_work_order_entity_or_404(db: Session, *, tenant_id: int, work_order_id: int) -> WorkOrder:
    wo = db.execute(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if wo is None:
        raise DomainError("OS não encontrada")
    return wo


def get_work_order_or_404(db: Session, *, tenant_id: int, work_order_id: int) -> dict:
    row = db.execute(
        _enriched_work_order_stmt(tenant_id=tenant_id).where(WorkOrder.id == work_order_id)
    ).mappings().one_or_none()
    if row is None:
        raise DomainError("OS não encontrada")
    return _serialize_work_order_row(row)


def get_active_session_for_technician(db: Session, *, technician_id: int) -> ExecutionSession | None:
    return db.execute(
        select(ExecutionSession).where(
            ExecutionSession.technician_id == technician_id,
            ExecutionSession.ended_at.is_(None),
        )
    ).scalar_one_or_none()


def _ensure_can_execute(current_user: User) -> None:
    if not user_has_any_role(current_user, ["tecnico"]):
        raise DomainError("Apenas técnico pode executar OS")


def start_work_order(db: Session, *, current_user: User, work_order_id: int) -> WorkOrder:
    current_user = db.execute(_with_roles_stmt(current_user.id)).scalar_one()
    _ensure_can_execute(current_user)

    wo = get_work_order_entity_or_404(db, tenant_id=current_user.tenant_id, work_order_id=work_order_id)

    if wo.status not in {WorkOrderStatus.ABERTA, WorkOrderStatus.SUSPENSA}:
        raise DomainError("OS não pode ser iniciada/retomada neste status")

    active = get_active_session_for_technician(db, technician_id=current_user.id)
    if active and active.work_order_id != wo.id:
        other = get_work_order_entity_or_404(db, tenant_id=current_user.tenant_id, work_order_id=active.work_order_id)
        raise DomainError(BLOCK_MESSAGE.format(code=other.code))

    if active is None:
        db.add(
            ExecutionSession(
                tenant_id=current_user.tenant_id,
                work_order_id=wo.id,
                technician_id=current_user.id,
            )
        )

    event_type = WorkOrderEventType.STARTED if wo.status == WorkOrderStatus.ABERTA else WorkOrderEventType.RESUMED
    wo.status = WorkOrderStatus.EM_EXECUCAO
    wo.technician_current_id = current_user.id

    add_event(db, work_order_id=wo.id, actor_user_id=current_user.id, event_type=event_type)

    db.commit()
    db.refresh(wo)
    return wo


def suspend_work_order(db: Session, *, current_user: User, work_order_id: int, payload: WorkOrderSuspend) -> WorkOrder:
    current_user = db.execute(_with_roles_stmt(current_user.id)).scalar_one()
    _ensure_can_execute(current_user)

    wo = get_work_order_entity_or_404(db, tenant_id=current_user.tenant_id, work_order_id=work_order_id)

    if wo.status != WorkOrderStatus.EM_EXECUCAO:
        raise DomainError("Somente OS em execução pode ser suspensa")
    if wo.technician_current_id != current_user.id:
        raise DomainError("Somente o técnico atuando pode suspender")

    session = get_active_session_for_technician(db, technician_id=current_user.id)
    if session is None or session.work_order_id != wo.id:
        raise DomainError("Sessão ativa não encontrada para esta OS")

    session.ended_at = utcnow()
    wo.status = WorkOrderStatus.SUSPENSA
    wo.technician_current_id = None

    add_event(
        db,
        work_order_id=wo.id,
        actor_user_id=current_user.id,
        event_type=WorkOrderEventType.SUSPENDED,
        description=payload.description,
        payload={"reason": payload.reason, "description": payload.description},
    )

    db.commit()
    db.refresh(wo)
    return wo


def finalize_work_order(db: Session, *, current_user: User, work_order_id: int, payload: WorkOrderFinalize) -> WorkOrder:
    current_user = db.execute(_with_roles_stmt(current_user.id)).scalar_one()
    _ensure_can_execute(current_user)

    wo = get_work_order_entity_or_404(db, tenant_id=current_user.tenant_id, work_order_id=work_order_id)

    if wo.status != WorkOrderStatus.EM_EXECUCAO:
        raise DomainError("Somente OS em execução pode ser finalizada")
    if wo.technician_current_id != current_user.id:
        raise DomainError("Somente o técnico atuando pode finalizar")

    session = get_active_session_for_technician(db, technician_id=current_user.id)
    if session is None or session.work_order_id != wo.id:
        raise DomainError("Sessão ativa não encontrada para esta OS")

    technician_minutes = None
    if wo.type == WorkOrderType.OSC:
        if payload.technician_downtime is None:
            raise DomainError("Parada(Técnico) é obrigatória para OSC")
        technician_minutes = payload.technician_downtime.total_minutes
        if technician_minutes <= 1:
            raise DomainError("Parada(Técnico) deve ser maior que 1 minuto para OSC")

    session.ended_at = utcnow()
    wo.status = WorkOrderStatus.FINALIZADA
    wo.technician_current_id = None
    wo.happened_what = payload.happened_what
    wo.happened_why = payload.happened_why
    wo.action_taken = payload.action_taken
    wo.technician_downtime_minutes = technician_minutes
    wo.finalization_at = utcnow()

    add_event(
        db,
        work_order_id=wo.id,
        actor_user_id=current_user.id,
        event_type=WorkOrderEventType.FINALIZED,
        payload={
            "happened_what": payload.happened_what,
            "happened_why": payload.happened_why,
            "action_taken": payload.action_taken,
            "technician_downtime_minutes": technician_minutes,
        },
    )

    db.commit()
    db.refresh(wo)
    return wo


def close_work_order(db: Session, *, current_user: User, work_order_id: int, payload: WorkOrderClose) -> WorkOrder:
    current_user = db.execute(_with_roles_stmt(current_user.id)).scalar_one()
    wo = get_work_order_entity_or_404(db, tenant_id=current_user.tenant_id, work_order_id=work_order_id)

    can_close_any = user_has_any_role(
        current_user,
        ["administrativo", "admin_tenant", "coordenador_manutencao"],
    )
    is_own_request = wo.requester_id == current_user.id

    if not (can_close_any or is_own_request):
        raise DomainError("Você não tem permissão para encerrar esta OS")

    if wo.type in {WorkOrderType.OSP, WorkOrderType.CHECKLIST}:
        raise DomainError("OSP e Checklist não possuem etapa Encerrada")

    if wo.status != WorkOrderStatus.FINALIZADA:
        raise DomainError("Somente OS finalizada pode ser encerrada")

    requester_minutes = payload.requester_downtime.total_minutes

    wo.status = WorkOrderStatus.ENCERRADA
    wo.met_expectation = payload.met_expectation
    wo.requester_downtime_minutes = requester_minutes
    wo.closure_at = utcnow()

    add_event(
        db,
        work_order_id=wo.id,
        actor_user_id=current_user.id,
        event_type=WorkOrderEventType.CLOSED,
        payload={
            "met_expectation": payload.met_expectation,
            "requester_downtime_minutes": requester_minutes,
        },
    )

    if payload.met_expectation is False:
        new_revision = wo.revision_number + 1
        revised = WorkOrder(
            tenant_id=wo.tenant_id,
            type=wo.type,
            status=WorkOrderStatus.ABERTA,
            sequence_number=wo.sequence_number,
            revision_number=new_revision,
            code=make_code(wo.type, wo.sequence_number, new_revision),
            requester_id=wo.requester_id,
            asset_id=wo.asset_id,
            description=wo.description,
            scheduled_date=wo.scheduled_date,
            machine_stopped=wo.machine_stopped,
        )
        db.add(revised)
        db.flush()

        add_event(
            db,
            work_order_id=revised.id,
            actor_user_id=current_user.id,
            event_type=WorkOrderEventType.REVISION_CREATED,
            payload={
                "source_work_order_id": wo.id,
                "source_work_order_code": wo.code,
                "revision_number": new_revision,
            },
        )

    db.commit()
    db.refresh(wo)
    return wo


def get_execution_now(db: Session, *, tenant_id: int):
    stmt = (
        select(
            ExecutionSession.technician_id,
            WorkOrder.id.label("work_order_id"),
            WorkOrder.code.label("work_order_code"),
            WorkOrder.asset_id.label("asset_id"),
            ExecutionSession.started_at,
            func.extract("epoch", func.now() - ExecutionSession.started_at).label("elapsed_seconds"),
        )
        .join(WorkOrder, WorkOrder.id == ExecutionSession.work_order_id)
        .where(
            ExecutionSession.tenant_id == tenant_id,
            ExecutionSession.ended_at.is_(None),
        )
        .order_by(ExecutionSession.started_at.asc())
    )
    return list(db.execute(stmt).all())