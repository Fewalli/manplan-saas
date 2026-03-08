from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WorkOrderEventType(str, enum.Enum):
    OPENED = "OPENED"
    STARTED = "STARTED"
    SUSPENDED = "SUSPENDED"
    RESUMED = "RESUMED"
    FINALIZED = "FINALIZED"
    CLOSED = "CLOSED"
    REVISION_CREATED = "REVISION_CREATED"
    DATE_CHANGED = "DATE_CHANGED"


class WorkOrderEvent(Base):
    __tablename__ = "work_order_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[WorkOrderEventType] = mapped_column(Enum(WorkOrderEventType), nullable=False, index=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    work_order = relationship("WorkOrder", back_populates="events")