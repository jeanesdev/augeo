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
    # Handle both /augeo and /augeo_db database names
    if "/augeo_db" in db_url:
        db_url = db_url.replace("/augeo_db", "/augeo_test_db")
    elif db_url.endswith("/augeo"):
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
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
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
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
        db=1,  # Use separate database for tests
    )

    yield client

    # Clear test database
    await client.flushdb()
    await client.close()  # type: ignore[attr-defined]


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
async def async_client(
    db_session: AsyncSession, redis_client: Redis
) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[type-arg]
    """
    Create async test client.

    Scope: function - new client for each test
    Use for tests that need async operations
    """

    from app.core.redis import get_redis

    # Override get_db dependency to use test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override get_redis dependency to use test Redis client (db=1)
    async def override_get_redis() -> Redis:  # type: ignore[type-arg]
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

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
async def test_super_admin_user(db_session: AsyncSession) -> Any:
    """
    Create a test super_admin user.

    Returns a User model instance with super_admin role.
    Password: TestPass123
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get super_admin role_id from database
    role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'super_admin'"))
    super_admin_role_id = role_result.scalar_one()

    # Create test super_admin user
    user = User(
        email="superadmin@test.com",
        first_name="Super",
        last_name="Admin",
        phone="+1-555-0001",
        password_hash=hash_password("TestPass123"),
        email_verified=True,
        is_active=True,
        role_id=super_admin_role_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_npo_admin_user(db_session: AsyncSession) -> Any:
    """
    Create a test npo_admin user.

    Returns a User model instance with npo_admin role and npo_id.
    Password: TestPass123
    """
    import uuid

    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get npo_admin role_id from database
    role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'npo_admin'"))
    npo_admin_role_id = role_result.scalar_one()

    # Create test NPO ID
    npo_id = uuid.uuid4()

    # Create test npo_admin user
    user = User(
        email="npoadmin@test.com",
        first_name="NPO",
        last_name="Admin",
        phone="+1-555-0002",
        password_hash=hash_password("TestPass123"),
        email_verified=True,
        is_active=True,
        role_id=npo_admin_role_id,
        npo_id=npo_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_npo_id(test_npo_admin_user: Any) -> Any:
    """
    Get the NPO ID from the test NPO admin user.
    """
    return test_npo_admin_user.npo_id


@pytest_asyncio.fixture
async def test_event_coordinator_user(db_session: AsyncSession, test_npo_id: Any) -> Any:
    """
    Create a test event_coordinator user.

    Returns a User model instance with event_coordinator role and npo_id.
    Password: TestPass123
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get event_coordinator role_id from database
    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE name = 'event_coordinator'")
    )
    event_coordinator_role_id = role_result.scalar_one()

    # Create test event_coordinator user
    user = User(
        email="eventcoordinator@test.com",
        first_name="Event",
        last_name="Coordinator",
        phone="+1-555-0003",
        password_hash=hash_password("TestPass123"),
        email_verified=True,
        is_active=True,
        role_id=event_coordinator_role_id,
        npo_id=test_npo_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_staff_user(db_session: AsyncSession, test_npo_id: Any) -> Any:
    """
    Create a test staff user.

    Returns a User model instance with staff role and npo_id.
    Password: TestPass123
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get staff role_id from database
    role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'staff'"))
    staff_role_id = role_result.scalar_one()

    # Create test staff user
    user = User(
        email="staff@test.com",
        first_name="Staff",
        last_name="Member",
        phone="+1-555-0004",
        password_hash=hash_password("TestPass123"),
        email_verified=True,
        is_active=True,
        role_id=staff_role_id,
        npo_id=test_npo_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_donor_user(db_session: AsyncSession) -> Any:
    """
    Create a test donor user.

    Returns a User model instance with donor role.
    Password: TestPass123
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.models.user import User

    # Get donor role_id from database
    role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
    donor_role_id = role_result.scalar_one()

    # Create test donor user
    user = User(
        email="donor@test.com",
        first_name="Donor",
        last_name="Person",
        phone="+1-555-0005",
        password_hash=hash_password("TestPass123"),
        email_verified=False,
        is_active=True,
        role_id=donor_role_id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_super_admin_token(async_client: AsyncClient, test_super_admin_user: Any) -> str:
    """Get access token for test super_admin user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_super_admin_user.email,
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_npo_admin_token(async_client: AsyncClient, test_npo_admin_user: Any) -> str:
    """Get access token for test npo_admin user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_npo_admin_user.email,
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_event_coordinator_token(
    async_client: AsyncClient, test_event_coordinator_user: Any
) -> str:
    """Get access token for test event_coordinator user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_event_coordinator_user.email,
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_staff_token(async_client: AsyncClient, test_staff_user: Any) -> str:
    """Get access token for test staff user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_staff_user.email,
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_donor_token(async_client: AsyncClient, test_donor_user: Any) -> str:
    """Get access token for test donor user."""
    # First set donor as verified and active to allow login
    test_donor_user.email_verified = True
    test_donor_user.is_active = True

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_donor_user.email,
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


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
