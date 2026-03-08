from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkOrderCounter(Base):
    __tablename__ = "work_order_counters"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_work_order_counters_tenant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)