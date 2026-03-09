from datetime import datetime

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    area_id: int
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=150)


class AssetRead(BaseModel):
    id: int
    area_id: int
    area_code: str
    area_name: str
    code: str
    name: str
    location: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class AssetHistoryItem(BaseModel):
    id: int
    code: str
    type: str
    status: str
    description: str
    created_at: datetime
    finalization_at: datetime | None = None
    closure_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssetDetail(BaseModel):
    id: int
    area_id: int
    area_code: str
    area_name: str
    code: str
    name: str
    location: str | None
    is_active: bool
    recent_work_orders: list[AssetHistoryItem]