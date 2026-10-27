import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.adapters.outbound.cache.rate_limit import rate_limiter
from app.infrastructure.logging import get_logger

logger = get_logger("middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()

        client = request.client.host if request.client else "unknown"
        if not await rate_limiter.allow(f"{client}:{request.url.path}"):
            return JSONResponse(
                status_code=429,
                content={"code": "rate_limited", "message": "Too many requests", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )
        return response
