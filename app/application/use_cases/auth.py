from app.application.ports.repositories import UserRepository
from app.application.ports.security import PasswordHasher, TokenService
from app.domain.entities import Role, TokenPair, User
from app.domain.errors import AuthError, ConflictError, ValidationDomainError


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, email: str, password: str, full_name: str, role: Role = Role.OPERATOR) -> User:
        if len(password) < 8:
            raise ValidationDomainError("Password must have at least 8 characters")
        existing = await self._users.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")
        return await self._users.create(
            email=email,
            full_name=full_name,
            hashed_password=self._hasher.hash(password),
            role=role,
        )


class LoginUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if not user or not self._hasher.verify(password, user.hashed_password):
            raise AuthError("Invalid credentials")
        if not user.is_active:
            raise AuthError("User inactive")
        return self._tokens.create_token_pair(user)


class RefreshAccessToken:
    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def execute(self, refresh_token: str) -> dict:
        payload = self._tokens.decode_refresh(refresh_token)
        user = await self._users.get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise AuthError("Invalid refresh token")
        access = self._tokens.create_access_from_refresh(refresh_token, user.role, user.email)
        return {"access_token": access, "token_type": "bearer"}
