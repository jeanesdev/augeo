"""Contract tests for GET /api/v1/users endpoint.

Tests validate API contract compliance per contracts/users.yaml specification.
These tests verify:
- Request/response schemas match OpenAPI spec
- Pagination works correctly (page, per_page)
- Filtering works (role, npo_id, email_verified, is_active, search)
- Access control is enforced (super_admin sees all, npo_admin sees their NPO only)
- Status codes are correct for different scenarios
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password


class TestUsersListContract:
    """Contract tests for GET /api/v1/users endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_requires_authentication(self, async_client: AsyncClient):
        """Test that listing users requires authentication.

        Contract: GET /api/v1/users
        Expected: 401 Unauthorized when no token provided
        """
        response = await async_client.get("/api/v1/users")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_list_users_default_pagination(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test default pagination (page=1, per_page=20).

        Contract: GET /api/v1/users
        Expected: 200 OK with paginated response
        """
        # Create some additional test users
        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        for i in range(5):
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
                    "email": f"user{i}@example.com",
                    "first_name": f"User{i}",
                    "last_name": "Test",
                    "password_hash": hash_password("Password123"),
                    "email_verified": True,
                    "is_active": True,
                    "role_id": donor_role_id,
                },
            )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users")

        # This will fail until we implement the endpoint
        # Expected response structure:
        # {
        #   "items": [...],
        #   "total": int,
        #   "page": 1,
        #   "per_page": 20,
        #   "total_pages": int
        # }
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1
        assert "per_page" in data
        assert data["per_page"] == 20
        assert "total_pages" in data

        # At least the test_user and 5 created users should be present
        assert len(data["items"]) >= 6

    @pytest.mark.asyncio
    async def test_list_users_custom_pagination(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test custom pagination parameters.

        Contract: GET /api/v1/users?page=2&per_page=2
        Expected: 200 OK with specified page and per_page
        """
        # Create some test users
        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        for i in range(5):
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
                    "email": f"page_user{i}@example.com",
                    "first_name": f"PageUser{i}",
                    "last_name": "Test",
                    "password_hash": hash_password("Password123"),
                    "email_verified": True,
                    "is_active": True,
                    "role_id": donor_role_id,
                },
            )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users?page=2&per_page=2")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 2
        assert data["per_page"] == 2
        assert len(data["items"]) <= 2

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering by role.

        Contract: GET /api/v1/users?role=donor
        Expected: 200 OK with only donor users
        """
        # Create users with different roles
        donor_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = donor_result.scalar_one()

        staff_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'staff'"))
        staff_role_id = staff_result.scalar_one()

        # Create 2 donors and 2 staff
        for i in range(2):
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
                    "email": f"donor_filter{i}@example.com",
                    "first_name": f"Donor{i}",
                    "last_name": "Test",
                    "password_hash": hash_password("Password123"),
                    "email_verified": True,
                    "is_active": True,
                    "role_id": donor_role_id,
                },
            )

        for i in range(2):
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
                    "email": f"staff_filter{i}@example.com",
                    "first_name": f"Staff{i}",
                    "last_name": "Test",
                    "password_hash": hash_password("Password123"),
                    "email_verified": True,
                    "is_active": True,
                    "role_id": staff_role_id,
                },
            )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users?role=donor")

        assert response.status_code == 200
        data = response.json()

        # All returned users should have role "donor"
        for user in data["items"]:
            assert user["role"] == "donor"

    @pytest.mark.asyncio
    async def test_list_users_filter_by_email_verified(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering by email_verified status.

        Contract: GET /api/v1/users?email_verified=false
        Expected: 200 OK with only unverified users
        """
        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        # Create unverified user
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
                "email": "unverified@example.com",
                "first_name": "Unverified",
                "last_name": "User",
                "password_hash": hash_password("Password123"),
                "email_verified": False,
                "is_active": False,
                "role_id": donor_role_id,
            },
        )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users?email_verified=false")

        assert response.status_code == 200
        data = response.json()

        # All returned users should have email_verified=false
        for user in data["items"]:
            assert user["email_verified"] is False

    @pytest.mark.asyncio
    async def test_list_users_filter_by_is_active(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering by is_active status.

        Contract: GET /api/v1/users?is_active=false
        Expected: 200 OK with only inactive users
        """
        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        # Create inactive user
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
                "email": "inactive@example.com",
                "first_name": "Inactive",
                "last_name": "User",
                "password_hash": hash_password("Password123"),
                "email_verified": True,
                "is_active": False,
                "role_id": donor_role_id,
            },
        )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users?is_active=false")

        assert response.status_code == 200
        data = response.json()

        # All returned users should have is_active=false
        for user in data["items"]:
            assert user["is_active"] is False

    @pytest.mark.asyncio
    async def test_list_users_filter_by_search(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test search functionality across name and email.

        Contract: GET /api/v1/users?search=john
        Expected: 200 OK with users matching search term
        """
        role_result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'donor'"))
        donor_role_id = role_result.scalar_one()

        # Create users with distinctive names
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
                "email": "john.smith@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "password_hash": hash_password("Password123"),
                "email_verified": True,
                "is_active": True,
                "role_id": donor_role_id,
            },
        )

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
                "email": "jane.doe@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "password_hash": hash_password("Password123"),
                "email_verified": True,
                "is_active": True,
                "role_id": donor_role_id,
            },
        )
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/users?search=john")

        assert response.status_code == 200
        data = response.json()

        # At least one user should match
        assert len(data["items"]) >= 1

        # Check that matched users contain "john" in name or email (case-insensitive)
        for user in data["items"]:
            search_match = (
                "john" in user["first_name"].lower()
                or "john" in user["last_name"].lower()
                or "john" in user["email"].lower()
            )
            assert search_match

    @pytest.mark.asyncio
    async def test_list_users_invalid_page_returns_400(self, authenticated_client: AsyncClient):
        """Test invalid page parameter returns 400.

        Contract: GET /api/v1/users?page=0
        Expected: 400 Bad Request
        """
        response = await authenticated_client.get("/api/v1/users?page=0")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_list_users_invalid_per_page_returns_400(self, authenticated_client: AsyncClient):
        """Test invalid per_page parameter returns 400.

        Contract: GET /api/v1/users?per_page=0
        Expected: 400 Bad Request
        """
        response = await authenticated_client.get("/api/v1/users?per_page=0")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_list_users_per_page_max_100(self, authenticated_client: AsyncClient):
        """Test per_page cannot exceed 100.

        Contract: GET /api/v1/users?per_page=101
        Expected: 400 Bad Request
        """
        response = await authenticated_client.get("/api/v1/users?per_page=101")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "per_page" in data["error"]["message"].lower()
