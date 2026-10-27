from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.domain.entities import Role, TokenPair, User
from app.domain.errors import AuthError
from app.infrastructure.config import get_settings

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasslibPasswordHasher:
    def hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)


class JoseTokenService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _encode(self, payload: dict, expires_delta: timedelta) -> str:
        data = payload.copy()
        data["exp"] = datetime.now(timezone.utc) + expires_delta
        return jwt.encode(data, self._settings.secret_key, algorithm=ALGORITHM)

    def create_token_pair(self, user: User) -> TokenPair:
        access = self._encode(
            {"sub": str(user.id), "email": user.email, "role": user.role.value, "type": "access"},
            timedelta(minutes=self._settings.access_token_expire_minutes),
        )
        refresh = self._encode(
            {"sub": str(user.id), "email": user.email, "role": user.role.value, "type": "refresh"},
            timedelta(days=self._settings.refresh_token_expire_days),
        )
        return TokenPair(access_token=access, refresh_token=refresh)

    def decode_access(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._settings.secret_key, algorithms=[ALGORITHM])
        except JWTError as exc:
            raise AuthError("Invalid access token") from exc
        if payload.get("type") != "access":
            raise AuthError("Invalid access token type")
        return payload

    def decode_refresh(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._settings.secret_key, algorithms=[ALGORITHM])
        except JWTError as exc:
            raise AuthError("Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise AuthError("Invalid refresh token type")
        return payload

    def create_access_from_refresh(self, refresh_token: str, role: Role, email: str) -> str:
        payload = self.decode_refresh(refresh_token)
        return self._encode(
            {
                "sub": payload["sub"],
                "email": email,
                "role": role.value,
                "type": "access",
            },
            timedelta(minutes=self._settings.access_token_expire_minutes),
        )
