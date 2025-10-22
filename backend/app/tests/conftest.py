"""Pytest configuration and fixtures."""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from redis.asyncio import Redis  # type: ignore[import-untyped]
from sqlalchemy import text
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
    Ensures asyncpg driver is used for async SQLAlchemy.
    """
    # Replace database name with test database
    db_url: str = str(settings.database_url)
    if db_url.endswith("/augeo"):
        db_url = db_url.replace("/augeo", "/augeo_test")

    # Ensure we're using postgresql+asyncpg:// not postgresql://
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    return db_url


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine.

    Scope: session - one engine for all tests
    Uses NullPool to avoid connection pooling in tests
    """
    engine = create_async_engine(test_database_url, poolclass=NullPool, echo=False)

    # Create all tables including roles
    async with engine.begin() as conn:
        # First create roles table (required by users table FK)
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    scope VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT role_name_valid CHECK (name IN ('super_admin', 'npo_admin', 'event_coordinator', 'staff', 'donor')),
                    CONSTRAINT role_scope_valid CHECK (scope IN ('platform', 'npo', 'event', 'own'))
                )
            """
            )
        )

        # Seed roles
        await conn.execute(
            text(
                """
                INSERT INTO roles (name, description, scope) VALUES
                    ('super_admin', 'Augeo platform staff with full access to all NPOs and events', 'platform'),
                    ('npo_admin', 'Full management access within assigned nonprofit organization(s)', 'npo'),
                    ('event_coordinator', 'Event and auction management within assigned NPO', 'npo'),
                    ('staff', 'Donor registration and check-in within assigned events', 'event'),
                    ('donor', 'Bidding and profile management only', 'own')
                ON CONFLICT (name) DO NOTHING
            """
            )
        )

        # Reflect the roles table into Base.metadata so auth_service can use it
        await conn.run_sync(lambda sync_conn: Base.metadata.reflect(bind=sync_conn, only=["roles"]))

        # Then create other tables
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS roles CASCADE"))

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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> Any:
    """
    Create a test user for authentication tests.

    Returns a User model instance with verified email and active status.
    Password: TestPass123
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get donor role_id from database
    role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
    donor_role_id = role_result.scalar_one()

    # Create test user
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="+1-555-0100",
        password_hash=hash_password("TestPass123"),
        email_verified=True,
        is_active=True,
        role_id=donor_role_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def authenticated_client(async_client: AsyncClient, test_user: Any) -> AsyncClient:
    """
    Create authenticated async test client with access token.

    Returns AsyncClient with Authorization header set to valid access token.
    """
    # Clear rate limiting from Redis to avoid conflicts from previous test runs
    from app.core.redis import get_redis

    redis_client = await get_redis()
    await redis_client.flushdb()

    # Login to get access token
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "TestPass123",
        },
    )

    assert response.status_code == 200, f"Login failed: {response.json()}"
    data = response.json()
    access_token = data["access_token"]

    # Set authorization header for subsequent requests
    async_client.headers["Authorization"] = f"Bearer {access_token}"

    return async_client
