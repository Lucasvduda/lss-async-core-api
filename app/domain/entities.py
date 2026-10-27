from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


@dataclass
class User:
    id: int
    email: str
    full_name: str
    role: Role
    hashed_password: str
    is_active: bool
    created_at: datetime


@dataclass
class Item:
    id: int
    title: str
    description: str | None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
