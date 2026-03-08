from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WorkOrderType(str, enum.Enum):
    OSC = "OSC"
    OSCP = "OSCP"
    OSM = "OSM"
    OSP = "OSP"
    CHECKLIST = "CHECKLIST"


class WorkOrderStatus(str, enum.Enum):
    ABERTA = "ABERTA"
    EM_EXECUCAO = "EM_EXECUCAO"
    SUSPENSA = "SUSPENSA"
    FINALIZADA = "FINALIZADA"
    ENCERRADA = "ENCERRADA"
    EXECUTADO = "EXECUTADO"


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_work_orders_tenant_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    type: Mapped[WorkOrderType] = mapped_column(Enum(WorkOrderType), nullable=False, index=True)
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus),
        nullable=False,
        default=WorkOrderStatus.ABERTA,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    technician_current_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    machine_stopped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    happened_what: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    happened_why: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    technician_downtime_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requester_downtime_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    met_expectation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    finalization_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requester = relationship("User", foreign_keys=[requester_id])
    technician_current = relationship("User", foreign_keys=[technician_current_id])
    events = relationship("WorkOrderEvent", back_populates="work_order", cascade="all, delete-orphan")
    execution_sessions = relationship("ExecutionSession", back_populates="work_order", cascade="all, delete-orphan")