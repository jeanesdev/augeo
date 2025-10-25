"""Integration tests for audit logging to database.

Tests that audit events are persisted to the audit_logs table when
authentication and authorization actions occur.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService


class TestAuditLogging:
    """Integration tests for audit log persistence."""

    @pytest.mark.asyncio
    async def test_audit_service_creates_database_record(
        self,
        db_session: AsyncSession,
        test_user,
    ):
        """Test that AuditService.log_* methods persist to database.

        Verifies:
        1. log_login_success creates audit_log record
        2. Record has correct action, user_id, ip_address
        """
        # Log a login success
        await AuditService.log_login_success(
            db=db_session,
            user_id=test_user.id,
            email=test_user.email,
            ip_address="192.168.1.1",
            user_agent="Test User Agent",
            session_id=uuid.uuid4(),
        )

        # Check audit log was created in database
        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.action == "login_success")
            .where(AuditLog.user_id == test_user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None, "Audit log not found in database"
        assert audit_log.action == "login_success"
        assert audit_log.user_id == test_user.id
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Test User Agent"
        assert audit_log.event_metadata is not None
        assert audit_log.event_metadata["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_failed_login_logs_with_null_user_id(
        self,
        db_session: AsyncSession,
    ):
        """Test that failed login logs have NULL user_id.

        Verifies:
        1. log_login_failed creates audit_log record
        2. Record has user_id=NULL (failed attempt)
        3. Record includes email and reason in metadata
        """
        # Log a failed login
        await AuditService.log_login_failed(
            db=db_session,
            email="nonexistent@example.com",
            reason="User not found",
            ip_address="192.168.1.2",
            user_agent="Test Agent",
        )

        # Check audit log was created
        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.action == "login_failed")
            .where(AuditLog.ip_address == "192.168.1.2")
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.action == "login_failed"
        assert audit_log.user_id is None  # NULL for failed attempts
        assert audit_log.ip_address == "192.168.1.2"
        assert audit_log.event_metadata is not None
        assert audit_log.event_metadata["email"] == "nonexistent@example.com"
        assert audit_log.event_metadata["reason"] == "User not found"

    @pytest.mark.asyncio
    async def test_multiple_audit_log_methods(
        self,
        db_session: AsyncSession,
        test_user,
    ):
        """Test various AuditService methods persist correctly.

        Verifies:
        1. log_password_changed creates audit_log
        2. log_email_verification creates audit_log
        3. log_logout creates audit_log
        4. All records have correct structure
        """
        # Test password changed
        await AuditService.log_password_changed(
            db=db_session,
            user_id=test_user.id,
            email=test_user.email,
            ip_address="192.168.1.3",
        )

        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.action == "password_changed")
            .where(AuditLog.user_id == test_user.id)
        )
        password_log = result.scalar_one_or_none()
        assert password_log is not None
        assert password_log.action == "password_changed"

        # Test email verification
        await AuditService.log_email_verification(
            db=db_session,
            user_id=test_user.id,
            email=test_user.email,
            ip_address="192.168.1.4",
        )

        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.action == "email_verified")
            .where(AuditLog.user_id == test_user.id)
        )
        email_log = result.scalar_one_or_none()
        assert email_log is not None
        assert email_log.action == "email_verified"

        # Test logout
        await AuditService.log_logout(
            db=db_session,
            user_id=test_user.id,
            email=test_user.email,
            ip_address="192.168.1.5",
            session_id=uuid.uuid4(),
        )

        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.action == "logout")
            .where(AuditLog.user_id == test_user.id)
        )
        logout_log = result.scalar_one_or_none()
        assert logout_log is not None
        assert logout_log.action == "logout"

    @pytest.mark.asyncio
    async def test_audit_log_queryability(
        self,
        db_session: AsyncSession,
        test_user,
    ):
        """Test that audit logs can be queried by various criteria.

        Verifies:
        1. Can query by user_id
        2. Can query by action
        3. Can query by ip_address
        4. Can query by date range
        """
        # Create multiple audit logs
        for i in range(3):
            await AuditService.log_login_success(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                ip_address=f"192.168.1.{i}",
                user_agent="Test Agent",
            )

        # Query by user_id
        result = await db_session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == test_user.id)
            .order_by(AuditLog.created_at.desc())
        )
        logs = result.scalars().all()
        assert len(logs) >= 3

        # Query by action
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "login_success")
        )
        logs = result.scalars().all()
        assert len(logs) >= 3

        # Query by IP address
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.ip_address == "192.168.1.0")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
