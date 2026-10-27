from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.domain.entities import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: Role = Role.OPERATOR


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class ItemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: str = "open"


class ItemResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class PaginatedItems(BaseModel):
    items: list[ItemResponse]
    page: int
    page_size: int
    total: int
    pages: int


class ImportResult(BaseModel):
    imported: int


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str | None = None
