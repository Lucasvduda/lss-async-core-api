import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_async_core.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

from app.adapters.outbound.persistence.database import engine, init_db  # noqa: E402
from app.adapters.outbound.persistence.models import Base  # noqa: E402
from app.infrastructure.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
