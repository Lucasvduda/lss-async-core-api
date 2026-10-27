from fastapi import APIRouter, Depends

from app.adapters.inbound.api.deps import get_current_user, get_user_repo, password_hasher, token_service
from app.adapters.inbound.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.adapters.outbound.persistence.repositories import SqlAlchemyUserRepository
from app.application.use_cases.auth import LoginUser, RefreshAccessToken, RegisterUser
from app.domain.entities import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> UserResponse:
    user = await RegisterUser(users, password_hasher).execute(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=body.role,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> TokenResponse:
    pair = await LoginUser(users, password_hasher, token_service).execute(body.email, body.password)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> TokenResponse:
    data = await RefreshAccessToken(users, token_service).execute(body.refresh_token)
    return TokenResponse(access_token=data["access_token"], token_type=data["token_type"])


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )
