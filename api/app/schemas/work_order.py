from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.work_order import WorkOrderStatus, WorkOrderType
from app.schemas.common_time import DurationDHM


class WorkOrderCreate(BaseModel):
    type: WorkOrderType
    description: str = Field(min_length=1)
    asset_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_by_type(self):
        if self.type in {WorkOrderType.OSC, WorkOrderType.OSCP} and not self.asset_id:
            raise ValueError("asset_id é obrigatório para OSC e OSCP")
        if self.type == WorkOrderType.OSCP and not self.scheduled_date:
            raise ValueError("scheduled_date é obrigatória para OSCP")
        return self


class WorkOrderSuspend(BaseModel):
    reason: str = Field(min_length=1)
    description: str = Field(min_length=1)


class WorkOrderFinalize(BaseModel):
    happened_what: str = Field(min_length=1)
    happened_why: str = Field(min_length=1)
    action_taken: str = Field(min_length=1)
    technician_downtime: Optional[DurationDHM] = None


class WorkOrderClose(BaseModel):
    met_expectation: bool
    requester_downtime: DurationDHM


class WorkOrderRead(BaseModel):
    id: int
    code: str
    type: WorkOrderType
    status: WorkOrderStatus
    requester_id: int
    asset_id: Optional[int]
    description: str
    scheduled_date: Optional[datetime]
    technician_current_id: Optional[int]
    technician_downtime_minutes: Optional[int]
    requester_downtime_minutes: Optional[int]
    met_expectation: Optional[bool]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionNowRead(BaseModel):
    technician_id: int
    work_order_id: int
    work_order_code: str
    asset_id: Optional[int]
    started_at: datetime
    elapsed_minutes: int

    model_config = {"from_attributes": True}