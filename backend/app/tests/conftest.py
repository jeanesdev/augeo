"""Pytest configuration and fixtures."""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from redis.asyncio import Redis  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base

settings = get_settings()

# ================================
# Event Loop Configuration
# ================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.

    Scope: session - one event loop for all tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ================================
# Database Fixtures
# ================================


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Get test database URL.

    Uses separate test database to avoid conflicts with development data.
    """
    # Replace database name with test database
    db_url: str = str(settings.database_url)
    if db_url.endswith("/augeo"):
        db_url = db_url.replace("/augeo", "/augeo_test")
    return db_url


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine.

    Scope: session - one engine for all tests
    Uses NullPool to avoid connection pooling in tests
    """
    engine = create_async_engine(test_database_url, poolclass=NullPool, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.

    Scope: function - new session for each test
    Uses transaction rollback to keep tests isolated
    """
    # Start a transaction
    connection = await test_engine.connect()
    transaction = await connection.begin()

    # Create session bound to transaction
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    # Rollback transaction and close connection
    await session.close()
    await transaction.rollback()
    await connection.close()


# ================================
# Redis Fixtures
# ================================


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator["Redis[Any]", None]:
    """
    Create Redis client for tests.

    Scope: function - new client for each test
    Uses database 1 for tests (default is 0)
    """
    client: Redis[Any] = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        db=1,  # Use separate database for tests
    )

    yield client

    # Clear test database
    await client.flushdb()
    await client.aclose()


# ================================
# FastAPI Client Fixtures
# ================================


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create synchronous test client.

    Scope: function - new client for each test
    Use for simple tests that don't need async
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client.

    Scope: function - new client for each test
    Use for tests that need async operations
    """

    # Override get_db dependency to use test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ================================
# Authentication Fixtures
# ================================
# TODO: Add fixtures for authenticated users when auth is implemented
# - authenticated_client: Client with valid access token
# - super_admin_client: Client with super admin role
# - npo_admin_client: Client with npo admin role
# - donor_client: Client with donor role
