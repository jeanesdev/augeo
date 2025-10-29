"""Integration tests for legal document management.

Tests the complete legal document CRUD flow:
- Creating draft documents
- Updating draft documents
- Publishing documents (with automatic archiving)
- Retrieving current published documents
- Retrieving specific versions
- Version history

This tests the integration of:
- API endpoints (legal_documents.py)
- Services (legal_document_service.py)
- Models (LegalDocument)
- Database (PostgreSQL with enums)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_document import LegalDocument, LegalDocumentStatus


class TestLegalDocumentFlow:
    """Integration tests for legal document CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_draft_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test creating a draft legal document (admin only)."""
        payload = {
            "document_type": "terms_of_service",
            "version": "1.0",
            "content": "# Terms of Service\n\nThese are the terms...",
        }

        response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
            headers=admin_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "terms_of_service"
        assert data["version"] == "1.0"
        assert data["status"] == "draft"
        assert data["published_at"] is None

        # Verify in database
        doc_id = uuid.UUID(data["id"])
        result = await db_session.execute(select(LegalDocument).where(LegalDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.status == LegalDocumentStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_duplicate_version_fails(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test that creating duplicate type+version fails."""
        payload = {
            "document_type": "privacy_policy",
            "version": "1.0",
            "content": "Privacy policy content",
        }

        # Create first document
        response1 = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
            headers=admin_auth_headers,
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
            headers=admin_auth_headers,
        )
        assert response2.status_code == 400
        detail = response2.json()["detail"]
        error_text = detail if isinstance(detail, str) else detail.get("message", "")
        assert "already exists" in error_text.lower()

    @pytest.mark.asyncio
    async def test_update_draft_document(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test updating a draft document."""
        # Create draft
        create_payload = {
            "document_type": "terms_of_service",
            "version": "2.0",
            "content": "Original content",
        }
        create_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=create_payload,
            headers=admin_auth_headers,
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["id"]

        # Update draft
        update_payload = {"content": "Updated content with more details"}
        update_response = await async_client.patch(
            f"/api/v1/legal/admin/documents/{doc_id}",
            json=update_payload,
            headers=admin_auth_headers,
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["content"] == "Updated content with more details"

    @pytest.mark.asyncio
    async def test_cannot_update_published_document(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test that published documents cannot be updated."""
        # Create and publish
        create_payload = {
            "document_type": "privacy_policy",
            "version": "2.0",
            "content": "Privacy policy v2",
        }
        create_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=create_payload,
            headers=admin_auth_headers,
        )
        doc_id = create_response.json()["id"]

        # Publish
        await async_client.post(
            f"/api/v1/legal/admin/documents/{doc_id}/publish",
            headers=admin_auth_headers,
        )

        # Try to update
        update_payload = {"content": "Trying to change published doc"}
        update_response = await async_client.patch(
            f"/api/v1/legal/admin/documents/{doc_id}",
            json=update_payload,
            headers=admin_auth_headers,
        )

        assert update_response.status_code == 400
        detail = update_response.json()["detail"]
        error_text = detail if isinstance(detail, str) else detail.get("message", "")
        assert "Only DRAFT documents" in error_text

    @pytest.mark.asyncio
    async def test_publish_document_archives_previous(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test that publishing a document archives the previous published version."""
        # Create and publish first version
        v1_payload = {
            "document_type": "terms_of_service",
            "version": "1.0",
            "content": "TOS v1.0",
        }
        v1_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=v1_payload,
            headers=admin_auth_headers,
        )
        v1_id = v1_response.json()["id"]

        publish_v1 = await async_client.post(
            f"/api/v1/legal/admin/documents/{v1_id}/publish",
            headers=admin_auth_headers,
        )
        assert publish_v1.status_code == 200

        # Create and publish second version
        v2_payload = {
            "document_type": "terms_of_service",
            "version": "1.1",
            "content": "TOS v1.1 with updates",
        }
        v2_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=v2_payload,
            headers=admin_auth_headers,
        )
        v2_id = v2_response.json()["id"]

        publish_v2 = await async_client.post(
            f"/api/v1/legal/admin/documents/{v2_id}/publish",
            headers=admin_auth_headers,
        )
        assert publish_v2.status_code == 200

        # Check v1 is now archived
        result = await db_session.execute(
            select(LegalDocument).where(LegalDocument.id == uuid.UUID(v1_id))
        )
        v1_doc = result.scalar_one()
        assert v1_doc.status == LegalDocumentStatus.ARCHIVED

        # Check v2 is published
        result = await db_session.execute(
            select(LegalDocument).where(LegalDocument.id == uuid.UUID(v2_id))
        )
        v2_doc = result.scalar_one()
        assert v2_doc.status == LegalDocumentStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_get_current_published_documents_public(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test public endpoint for getting current published documents."""
        # Create and publish TOS
        tos_payload = {
            "document_type": "terms_of_service",
            "version": "1.0",
            "content": "TOS content",
        }
        tos_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=tos_payload,
            headers=admin_auth_headers,
        )
        tos_id = tos_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{tos_id}/publish",
            headers=admin_auth_headers,
        )

        # Create and publish Privacy Policy
        privacy_payload = {
            "document_type": "privacy_policy",
            "version": "1.0",
            "content": "Privacy policy content",
        }
        privacy_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=privacy_payload,
            headers=admin_auth_headers,
        )
        privacy_id = privacy_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{privacy_id}/publish",
            headers=admin_auth_headers,
        )

        # Get current documents (no auth required)
        response = await async_client.get("/api/v1/legal/documents")

        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 2
        doc_types = {doc["document_type"] for doc in documents}
        assert "terms_of_service" in doc_types
        assert "privacy_policy" in doc_types

    @pytest.mark.asyncio
    async def test_get_document_by_type(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting current document by type (public endpoint)."""
        # Create and publish
        payload = {
            "document_type": "terms_of_service",
            "version": "3.0",
            "content": "TOS v3.0 content",
        }
        create_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
            headers=admin_auth_headers,
        )
        doc_id = create_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{doc_id}/publish",
            headers=admin_auth_headers,
        )

        # Get by type (no auth required)
        response = await async_client.get("/api/v1/legal/documents/terms_of_service")

        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "terms_of_service"
        assert data["version"] == "3.0"

    @pytest.mark.asyncio
    async def test_get_document_by_version(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test getting specific document version (public endpoint)."""
        # Create and publish v1.0
        v1_payload = {
            "document_type": "privacy_policy",
            "version": "1.0",
            "content": "Privacy v1.0",
        }
        v1_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=v1_payload,
            headers=admin_auth_headers,
        )
        v1_id = v1_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{v1_id}/publish",
            headers=admin_auth_headers,
        )

        # Create and publish v2.0
        v2_payload = {
            "document_type": "privacy_policy",
            "version": "2.0",
            "content": "Privacy v2.0",
        }
        v2_response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=v2_payload,
            headers=admin_auth_headers,
        )
        v2_id = v2_response.json()["id"]
        await async_client.post(
            f"/api/v1/legal/admin/documents/{v2_id}/publish",
            headers=admin_auth_headers,
        )

        # Get v1.0 specifically (no auth required)
        response = await async_client.get("/api/v1/legal/documents/privacy_policy/version/1.0")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"
        assert data["content"] == "Privacy v1.0"

    @pytest.mark.asyncio
    async def test_list_all_documents_admin(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Test admin endpoint for listing all documents with filters."""
        # Create multiple documents
        documents = [
            {"document_type": "terms_of_service", "version": "1.0", "content": "TOS 1.0"},
            {"document_type": "terms_of_service", "version": "2.0", "content": "TOS 2.0"},
            {"document_type": "privacy_policy", "version": "1.0", "content": "Privacy 1.0"},
        ]

        for doc_payload in documents:
            await async_client.post(
                "/api/v1/legal/admin/documents",
                json=doc_payload,
                headers=admin_auth_headers,
            )

        # List all documents
        response = await async_client.get(
            "/api/v1/legal/admin/documents",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

        # Filter by type
        tos_response = await async_client.get(
            "/api/v1/legal/admin/documents?document_type=terms_of_service",
            headers=admin_auth_headers,
        )

        assert tos_response.status_code == 200
        tos_data = tos_response.json()
        assert all(doc["document_type"] == "terms_of_service" for doc in tos_data["documents"])

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_documents(
        self,
        async_client: AsyncClient,
        user_auth_headers: dict[str, str],
    ) -> None:
        """Test that non-admin users cannot create documents."""
        payload = {
            "document_type": "terms_of_service",
            "version": "1.0",
            "content": "Unauthorized attempt",
        }

        response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
            headers=user_auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_admin_endpoints(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that unauthenticated users cannot access admin endpoints."""
        payload = {
            "document_type": "terms_of_service",
            "version": "1.0",
            "content": "Test",
        }

        response = await async_client.post(
            "/api/v1/legal/admin/documents",
            json=payload,
        )

        assert response.status_code == 401
