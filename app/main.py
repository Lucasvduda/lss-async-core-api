from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.inbound.api.v1 import auth as auth_router
from app.adapters.inbound.api.v1 import items as items_router
from app.adapters.outbound.cache.rate_limit import rate_limiter
from app.adapters.outbound.persistence.database import init_db
from app.infrastructure.config import get_settings
from app.infrastructure.exception_handlers import register_exception_handlers
from app.infrastructure.logging import setup_logging
from app.infrastructure.middleware import RequestContextMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    await init_db()
    await rate_limiter.connect()
    yield
    await rate_limiter.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API assíncrona da Lucas Software Solutions: JWT + refresh, RBAC, "
        "paginação com filtros, upload CSV, rate limiting e Clean Architecture."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)

app.include_router(auth_router.router, prefix="/v1")
app.include_router(items_router.router, prefix="/v1")


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}
