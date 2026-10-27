from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import (
    AuthError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error(request, 404, exc)

    @app.exception_handler(AuthError)
    async def auth_handler(request: Request, exc: AuthError) -> JSONResponse:
        return _error(request, 401, exc)

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return _error(request, 403, exc)

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return _error(request, 409, exc)

    @app.exception_handler(ValidationDomainError)
    async def validation_handler(request: Request, exc: ValidationDomainError) -> JSONResponse:
        return _error(request, 422, exc)

    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError) -> JSONResponse:
        return _error(request, 400, exc)


def _error(request: Request, status: int, exc: DomainError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status,
        content={"code": exc.code, "message": exc.message, "request_id": request_id},
    )
