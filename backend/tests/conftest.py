import os
import tempfile
import shutil
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db_session
from app.core.redis_client import get_redis_client, get_redis_pool
from app.core.config import settings


# Test database URL - use the same database but with transaction rollback
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/todoapp")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (sync fixture that returns engine)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    # Create all tables
    import asyncio
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    
    yield engine
    
    # Clean up
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(drop_tables())
    
    asyncio.run(engine.dispose())


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test, rollback at the end."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Begin a nested transaction
        async with session.begin_nested():
            yield session
        # Rollback the outer transaction
        await session.rollback()


@pytest.fixture
def redis_client() -> FakeAsyncRedis:
    """Create a fake Redis client for testing."""
    return FakeAsyncRedis(decode_responses=True)


@pytest.fixture(autouse=True)
async def override_dependencies(db_session: AsyncSession, redis_client: FakeAsyncRedis):
    """Override FastAPI dependencies for testing."""
    
    async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    def get_test_redis() -> FakeAsyncRedis:
        return redis_client
    
    app.dependency_overrides[get_db_session] = get_test_db
    app.dependency_overrides[get_redis_client] = get_test_redis
    app.dependency_overrides[get_redis_pool] = lambda: None  # Not used with fake redis
    
    # Override avatar upload path to temp directory
    temp_upload_dir = tempfile.mkdtemp()
    # Ensure the temp directory exists
    os.makedirs(temp_upload_dir, exist_ok=True)
    original_uploads_path = settings.avatar.uploads_path
    settings.avatar.uploads_path = temp_upload_dir
    
    yield
    
    # Cleanup
    app.dependency_overrides.clear()
    settings.avatar.uploads_path = original_uploads_path
    shutil.rmtree(temp_upload_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Placeholder for auth headers - will be set after login."""
    return {}


# Helper functions for tests
async def send_otp(async_client: AsyncClient, phone: str) -> dict:
    """Send OTP and return response."""
    response = await async_client.post("/auth/send-otp", json={"phone_number": phone})
    return response.json()


async def verify_otp(async_client: AsyncClient, phone: str, code: str, device_id: str) -> dict:
    """Verify OTP and return response with cookies."""
    headers = {"X-Device-Id": device_id}
    response = await async_client.post("/auth/verify-otp", json={"phone_number": phone, "code": code}, headers=headers)
    return {
        "json": response.json(),
        "cookies": dict(response.cookies),
        "status": response.status_code,
    }


async def refresh_token(async_client: AsyncClient, cookies: dict, csrf_token: str) -> dict:
    """Refresh access token."""
    headers = {"X-CSRF-Token": csrf_token}
    response = await async_client.post("/auth/refresh", cookies=cookies, headers=headers)
    return {
        "json": response.json() if response.status_code != 204 else {},
        "cookies": dict(response.cookies),
        "status": response.status_code,
    }


async def get_csrf_token(async_client: AsyncClient) -> dict:
    """Get CSRF token."""
    response = await async_client.get("/auth/csrf-token")
    return {
        "cookies": dict(response.cookies),
        "status": response.status_code,
    }