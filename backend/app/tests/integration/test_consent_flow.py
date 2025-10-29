"""Integration tests for consent management and GDPR compliance.

Tests the complete consent flow:
- Accepting legal documents
- Checking consent status
- Consent history tracking
- Withdrawing consent
- Data export requests
- Data deletion requests
- Consent check middleware (409 Conflict)

This tests the integration of:
- API endpoints (consent.py)
- Services (consent_service.py)
- Models (UserConsent, ConsentAuditLog)
- Middleware (consent_check.py)
- Database (PostgreSQL with audit triggers)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentAction, ConsentAuditLog, ConsentStatus, UserConsent


class TestConsentFlow:
    """Integration tests for consent management operations."""

    @pytest.mark.asyncio
    async def test_accept_consent_creates_record(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
    ) -> None:
        """Test that accepting consent creates database records."""
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }

        response = await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
        assert data["tos_document_id"] == published_legal_documents["tos_id"]

        # Verify in database
        consent_id = uuid.UUID(data["id"])
        result = await db_session.execute(select(UserConsent).where(UserConsent.id == consent_id))
        consent = result.scalar_one_or_none()
        assert consent is not None
        assert consent.status == ConsentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_accept_consent_supersedes_previous(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
        user_id: str,
    ) -> None:
        """Test that accepting new consent supersedes old active consent."""
        # Accept first consent
        payload1 = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }
        response1 = await async_client.post(
            "/api/v1/consent/accept",
            json=payload1,
            headers=user_auth_headers,
        )
        consent1_id = uuid.UUID(response1.json()["id"])

        # Create new document versions and publish
        # (In real scenario, admin would do this)
        # For test, we'll use the same documents and re-accept
        response2 = await async_client.post(
            "/api/v1/consent/accept",
            json=payload1,
            headers=user_auth_headers,
        )
        assert response2.status_code == 201

        # Check old consent is superseded
        result = await db_session.execute(select(UserConsent).where(UserConsent.id == consent1_id))
        old_consent = result.scalar_one()
        assert old_consent.status == ConsentStatus.SUPERSEDED

    @pytest.mark.asyncio
    async def test_accept_consent_creates_audit_log(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
        user_id: str,
    ) -> None:
        """Test that consent acceptance is logged in audit trail."""
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }

        await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )

        # Check audit log
        result = await db_session.execute(
            select(ConsentAuditLog)
            .where(ConsentAuditLog.user_id == uuid.UUID(user_id))
            .where(ConsentAuditLog.action == ConsentAction.CONSENT_GIVEN)
        )
        audit_logs = result.scalars().all()
        assert len(audit_logs) >= 1
        assert audit_logs[0].details is not None
        assert "tos_document_id" in audit_logs[0].details

    @pytest.mark.asyncio
    async def test_get_consent_status(
        self,
        async_client: AsyncClient,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
    ) -> None:
        """Test getting user's consent status."""
        # Accept consent first
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }
        await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )

        # Get status
        response = await async_client.get(
            "/api/v1/consent/status",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_active_consent"] is True
        assert data["consent_required"] is False
        assert data["current_tos_version"] == "1.0"
        assert data["current_privacy_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_consent_status_shows_outdated(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
    ) -> None:
        """Test that consent status detects outdated consent."""
        # User accepts v1.0
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }
        await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )

        # Admin publishes v2.0 of TOS
        new_tos_payload = {
            "document_type": "terms_of_service",
            "version": "2.0",
            "content": "Updated TOS v2.0",
        }
        create_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=new_tos_payload,
            headers=admin_auth_headers,
        )
        new_tos_id = create_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{new_tos_id}/publish",
            headers=admin_auth_headers,
        )

        # Check user's consent status
        response = await async_client.get(
            "/api/v1/consent/status",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_active_consent"] is True
        assert data["consent_required"] is True  # Outdated!
        assert data["current_tos_version"] == "1.0"
        assert data["latest_tos_version"] == "2.0"

    @pytest.mark.asyncio
    async def test_get_consent_history(
        self,
        async_client: AsyncClient,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
    ) -> None:
        """Test retrieving user's consent history."""
        # Accept consent twice
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }
        await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )
        await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )

        # Get history
        response = await async_client.get(
            "/api/v1/consent/history",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["consents"]) == 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_withdraw_consent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        published_legal_documents: dict[str, str],
        user_id: str,
    ) -> None:
        """Test withdrawing consent (GDPR right)."""
        # Accept consent first
        payload = {
            "tos_document_id": published_legal_documents["tos_id"],
            "privacy_document_id": published_legal_documents["privacy_id"],
        }
        accept_response = await async_client.post(
            "/api/v1/consent/accept",
            json=payload,
            headers=user_auth_headers,
        )
        consent_id = uuid.UUID(accept_response.json()["id"])

        # Withdraw consent
        response = await async_client.post(
            "/api/v1/consent/withdraw",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        assert "withdrawn" in response.json()["message"]

        # Check consent is withdrawn
        result = await db_session.execute(select(UserConsent).where(UserConsent.id == consent_id))
        consent = result.scalar_one()
        assert consent.status == ConsentStatus.WITHDRAWN
        assert consent.withdrawn_at is not None

        # Check user is deactivated
        from app.models.user import User

        user_result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_result.scalar_one()
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_request_data_export(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test GDPR data export request."""
        payload = {"email": None}  # Use default email

        response = await async_client.post(
            "/api/v1/consent/data-export",
            json=payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 202
        assert "export" in response.json()["message"].lower()

        # Check audit log
        result = await db_session.execute(
            select(ConsentAuditLog)
            .where(ConsentAuditLog.user_id == uuid.UUID(user_id))
            .where(ConsentAuditLog.action == ConsentAction.DATA_EXPORT_REQUESTED)
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None

    @pytest.mark.asyncio
    async def test_request_data_deletion(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_auth_headers: dict[str, str],
        user_id: str,
    ) -> None:
        """Test GDPR data deletion request (30-day grace period)."""
        payload = {"confirmation": True}

        response = await async_client.post(
            "/api/v1/consent/data-deletion",
            json=payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 202
        assert "30 days" in response.json()["message"]

        # Check audit log
        result = await db_session.execute(
            select(ConsentAuditLog)
            .where(ConsentAuditLog.user_id == uuid.UUID(user_id))
            .where(ConsentAuditLog.action == ConsentAction.DATA_DELETION_REQUESTED)
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None

        # Check user is deactivated
        from app.models.user import User

        user_result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_result.scalar_one()
        assert user.is_active is False

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_consent_endpoints(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that unauthenticated users cannot access consent endpoints."""
        response = await async_client.get("/api/v1/consent/status")

        assert response.status_code == 401
