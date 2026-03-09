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