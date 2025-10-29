"""Integration tests for cookie consent management (EU Cookie Law compliance).

Tests the complete cookie consent flow:
- Getting cookie consent (anonymous and authenticated)
- Setting cookie preferences
- Updating cookie preferences
- Revoking cookie consent
- Session-based consent for anonymous users
- User-based consent for authenticated users

This tests the integration of:
- API endpoints (cookies.py)
- Services (cookie_consent_service.py)
- Models (CookieConsent)
- Database (PostgreSQL with hybrid storage)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import CookieConsent


class TestCookieConsentFlow:
    """Integration tests for cookie consent operations."""

    @pytest.mark.asyncio
    async def test_get_cookie_consent_anonymous_default(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that anonymous users get default cookie consent (reject all)."""
        session_id = str(uuid.uuid4())

        response = await async_client.get(
            "/api/v1/cookies/consent",
            headers={"X-Session-ID": session_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["essential"] is True  # Always true
        assert data["analytics"] is False
        assert data["marketing"] is False
        assert data["has_consent"] is False  # No consent set yet

    @pytest.mark.asyncio
    async def test_set_cookie_consent_anonymous(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test setting cookie consent for anonymous user."""
        session_id = str(uuid.uuid4())
        payload = {
            "essential": True,
            "analytics": True,
            "marketing": False,
        }

        response = await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers={"X-Session-ID": session_id},
        )

        if response.status_code != 201:
            print(f"Error: {response.status_code} - {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == session_id
        assert data["analytics"] is True
        assert data["marketing"] is False

        # Verify in database
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.session_id == session_id)
        )
        consent = result.scalar_one_or_none()
        assert consent is not None
        assert consent.analytics is True

    @pytest.mark.asyncio
    async def test_set_cookie_consent_authenticated(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test setting cookie consent for authenticated user."""
        payload = {
            "essential": True,
            "analytics": True,
            "marketing": True,
        }

        response = await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert data["analytics"] is True
        assert data["marketing"] is True

        # Verify in database
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.user_id == uuid.UUID(user_id))
        )
        consent = result.scalar_one_or_none()
        assert consent is not None
        assert consent.marketing is True

    @pytest.mark.asyncio
    async def test_get_cookie_consent_authenticated(
        self,
        async_client: AsyncClient,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test getting cookie consent for authenticated user."""
        # Set consent first
        payload = {
            "essential": True,
            "analytics": True,
            "marketing": False,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers=user_auth_headers,
        )

        # Get consent
        response = await async_client.get(
            "/api/v1/cookies/consent",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_consent"] is True
        assert data["essential"] is True
        assert data["analytics"] is True
        assert data["marketing"] is False

    @pytest.mark.asyncio
    async def test_update_cookie_consent_authenticated(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test updating cookie preferences for authenticated user."""
        # Set initial consent
        initial_payload = {
            "essential": True,
            "analytics": False,
            "marketing": False,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=initial_payload,
            headers=user_auth_headers,
        )

        # Update consent
        update_payload = {
            "essential": True,
            "analytics": True,
            "marketing": True,
        }
        response = await async_client.put(
            "/api/v1/cookies/consent",
            json=update_payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analytics"] is True
        assert data["marketing"] is True

        # Verify in database
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.user_id == uuid.UUID(user_id))
        )
        consent = result.scalar_one()
        assert consent.analytics is True
        assert consent.marketing is True

    @pytest.mark.asyncio
    async def test_update_cookie_consent_anonymous(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test updating cookie preferences for anonymous user."""
        session_id = str(uuid.uuid4())

        # Set initial consent
        initial_payload = {
            "essential": True,
            "analytics": False,
            "marketing": False,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=initial_payload,
            headers={"X-Session-ID": session_id},
        )

        # Update consent
        update_payload = {
            "essential": True,
            "analytics": True,
            "marketing": False,
        }
        response = await async_client.put(
            "/api/v1/cookies/consent",
            json=update_payload,
            headers={"X-Session-ID": session_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analytics"] is True
        assert data["marketing"] is False

    @pytest.mark.asyncio
    async def test_revoke_cookie_consent_authenticated(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test revoking all cookie consent for authenticated user."""
        # Set consent first
        payload = {
            "essential": True,
            "analytics": True,
            "marketing": True,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers=user_auth_headers,
        )

        # Revoke consent
        response = await async_client.delete(
            "/api/v1/cookies/consent",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        assert "revoked" in response.json()["message"].lower()

        # Verify in database (should be set to reject all)
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.user_id == uuid.UUID(user_id))
        )
        consent = result.scalar_one()
        assert consent.analytics is False
        assert consent.marketing is False

    @pytest.mark.asyncio
    async def test_revoke_cookie_consent_anonymous(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test revoking all cookie consent for anonymous user."""
        session_id = str(uuid.uuid4())

        # Set consent first
        payload = {
            "essential": True,
            "analytics": True,
            "marketing": True,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers={"X-Session-ID": session_id},
        )

        # Revoke consent
        response = await async_client.delete(
            "/api/v1/cookies/consent",
            headers={"X-Session-ID": session_id},
        )

        assert response.status_code == 200

        # Verify in database
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.session_id == session_id)
        )
        consent = result.scalar_one()
        assert consent.analytics is False
        assert consent.marketing is False

    @pytest.mark.asyncio
    async def test_essential_cookies_always_true(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that essential cookies cannot be disabled."""
        session_id = str(uuid.uuid4())
        payload = {
            "essential": False,  # Try to disable
            "analytics": False,
            "marketing": False,
        }

        response = await async_client.post(
            "/api/v1/cookies/consent",
            json=payload,
            headers={"X-Session-ID": session_id},
        )

        # Should still succeed but essential forced to True
        assert response.status_code == 201
        data = response.json()
        assert data["essential"] is True  # Forced to True

    @pytest.mark.asyncio
    async def test_get_cookie_consent_requires_session_or_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that getting cookie consent requires session_id or auth."""
        response = await async_client.get("/api/v1/cookies/consent")

        # Should return 400 or default consent
        # Based on implementation, it should return default (reject all)
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_authenticated_user_migrates_session_consent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test that authenticated users can migrate their session consent."""
        session_id = str(uuid.uuid4())

        # Set consent as anonymous
        anonymous_payload = {
            "session_id": session_id,
            "essential": True,
            "analytics": True,
            "marketing": False,
        }
        await async_client.post(
            "/api/v1/cookies/consent",
            json=anonymous_payload,
        )

        # Now set consent as authenticated user (should override)
        auth_payload = {
            "essential": True,
            "analytics": True,
            "marketing": True,
        }
        response = await async_client.post(
            "/api/v1/cookies/consent",
            json=auth_payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert data["marketing"] is True  # Updated from anonymous

        # Verify authenticated consent is stored
        result = await db_session.execute(
            select(CookieConsent).where(CookieConsent.user_id == uuid.UUID(user_id))
        )
        consent = result.scalar_one_or_none()
        assert consent is not None
