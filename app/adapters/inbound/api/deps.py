from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.outbound.persistence.database import get_session
from app.adapters.outbound.persistence.repositories import SqlAlchemyItemRepository, SqlAlchemyUserRepository
from app.adapters.outbound.security.jwt_service import JoseTokenService, PasslibPasswordHasher
from app.domain.entities import Role, User
from app.domain.errors import AuthError, ForbiddenError

bearer = HTTPBearer(auto_error=False)
token_service = JoseTokenService()
password_hasher = PasslibPasswordHasher()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise AuthError("Missing bearer token")
    payload = token_service.decode_access(credentials.credentials)
    users = SqlAlchemyUserRepository(session)
    user = await users.get_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("User not found or inactive")
    return user


def require_roles(*roles: Role) -> Callable:
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles and user.role != Role.ADMIN:
            raise ForbiddenError(f"Requires one of roles: {[r.value for r in roles]}")
        return user

    return _checker


def get_user_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_item_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyItemRepository:
    return SqlAlchemyItemRepository(session)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")
