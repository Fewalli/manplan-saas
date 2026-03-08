from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_codes: list[str] = Field(default_factory=list)


class UserListItem(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    roles: list[str]