from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.execution_session import ExecutionSession


def assert_technician_has_no_active_execution(
    db: Session,
    *,
    tenant_id: int,
    technician_user_id: int,
) -> None:
    stmt: Select[tuple[ExecutionSession]] = (
        select(ExecutionSession)
        .where(ExecutionSession.tenant_id == tenant_id)
        .where(ExecutionSession.technician_id == technician_user_id)
        .where(ExecutionSession.ended_at.is_(None))
        .limit(1)
    )
    active = db.execute(stmt).scalar_one_or_none()
    if active is not None:
        raise ValueError(
            "Você já está em execução em outra OS. Suspenda a OS atual antes de iniciar outra."
        )