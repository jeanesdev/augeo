"""Contract tests for POST /api/v1/users endpoint.

Tests validate API contract compliance per contracts/users.yaml specification.
These tests verify:
- Request/response schemas match OpenAPI spec
- Only admins (super_admin, npo_admin) can create users
- Role assignment validation (npo_admin can only create within their NPO)
- npo_id constraints enforced (npo_admin/event_coordinator MUST have npo_id)
- Status codes are correct for different scenarios
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestUsersCreateContract:
    """Contract tests for POST /api/v1/users endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_requires_authentication(self, async_client: AsyncClient):
        """Test that creating users requires authentication.

        Contract: POST /api/v1/users
        Expected: 401 Unauthorized when no token provided
        """
        payload = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "donor",
        }
        response = await async_client.post("/api/v1/users", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_create_user_donor_role_forbidden(self, authenticated_client: AsyncClient):
        """Test that donor role cannot create users.

        Contract: POST /api/v1/users
        Expected: 403 Forbidden for non-admin roles
        """
        # authenticated_client uses test_user which has donor role
        payload = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "donor",
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert (
            "permission" in data["error"]["message"].lower()
            or "forbidden" in data["error"]["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_create_user_missing_required_fields_returns_400(
        self, authenticated_client: AsyncClient
    ):
        """Test that missing required fields returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request with validation errors
        """
        # Missing first_name
        payload = {
            "email": "incomplete@example.com",
            "last_name": "User",
            "role": "donor",
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_returns_400(self, authenticated_client: AsyncClient):
        """Test that invalid email format returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request with validation error
        """
        payload = {
            "email": "not-an-email",
            "first_name": "Test",
            "last_name": "User",
            "role": "donor",
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "email" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_role_returns_400(self, authenticated_client: AsyncClient):
        """Test that invalid role returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request with validation error
        """
        payload = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "invalid_role",
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "role" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_returns_409(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that duplicate email returns 409.

        Contract: POST /api/v1/users
        Expected: 409 Conflict
        """
        # Create a user first
        from app.core.security import hash_password

        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        await db_session.execute(
            text(
                """
                INSERT INTO users (email, first_name, last_name, password_hash,
                                 email_verified, is_active, role_id)
                VALUES (:email, :first_name, :last_name, :password_hash,
                       :email_verified, :is_active, :role_id)
            """
            ),
            {
                "email": "existing@example.com",
                "first_name": "Existing",
                "last_name": "User",
                "password_hash": hash_password("Password123"),
                "email_verified": True,
                "is_active": True,
                "role_id": donor_role_id,
            },
        )
        await db_session.commit()

        # Try to create user with same email
        payload = {
            "email": "existing@example.com",
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "donor",
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert (
            "email" in data["error"]["message"].lower()
            or "exists" in data["error"]["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_create_npo_admin_without_npo_id_returns_400(
        self, authenticated_client: AsyncClient
    ):
        """Test that creating npo_admin without npo_id returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request - npo_admin role requires npo_id
        """
        payload = {
            "email": "npoadmin@example.com",
            "first_name": "NPO",
            "last_name": "Admin",
            "role": "npo_admin",
            # Missing npo_id
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "npo_id" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_create_event_coordinator_without_npo_id_returns_400(
        self, authenticated_client: AsyncClient
    ):
        """Test that creating event_coordinator without npo_id returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request - event_coordinator role requires npo_id
        """
        payload = {
            "email": "coordinator@example.com",
            "first_name": "Event",
            "last_name": "Coordinator",
            "role": "event_coordinator",
            # Missing npo_id
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "npo_id" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_create_donor_with_npo_id_returns_400(self, authenticated_client: AsyncClient):
        """Test that creating donor with npo_id returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request - donor role must not have npo_id
        """
        payload = {
            "email": "donor@example.com",
            "first_name": "Invalid",
            "last_name": "Donor",
            "role": "donor",
            "npo_id": "550e8400-e29b-41d4-a716-446655440000",  # Should not be allowed
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "npo_id" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_create_staff_with_npo_id_returns_400(self, authenticated_client: AsyncClient):
        """Test that creating staff with npo_id returns 400.

        Contract: POST /api/v1/users
        Expected: 400 Bad Request - staff role must not have npo_id
        """
        payload = {
            "email": "staff@example.com",
            "first_name": "Invalid",
            "last_name": "Staff",
            "role": "staff",
            "npo_id": "550e8400-e29b-41d4-a716-446655440000",  # Should not be allowed
        }
        response = await authenticated_client.post("/api/v1/users", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "npo_id" in data["error"]["message"].lower()
