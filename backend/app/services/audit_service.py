"""Audit logging service for security events.

Logs authentication and authorization events for compliance and security monitoring.
Persists audit events to database and logs to structured logger.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events to log."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_REVOKED = "session_revoked"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_REACTIVATED = "account_reactivated"
    TOKEN_REFRESHED = "token_refreshed"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    ROLE_CHANGED = "role_changed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"


class AuditService:
    """Service for logging security and authentication audit events.

    Uses structured logging to capture security events with full context.
    In production, these logs should be sent to a SIEM or log aggregation service.
    """

    @staticmethod
    async def log_login_success(
        db: AsyncSession | None,
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: uuid.UUID | None = None,
    ) -> None:
        """Log successful login event to database and logger.

        Args:
            db: Database session for persisting audit log (optional for backward compatibility)
            user_id: UUID of authenticated user
            email: User's email address
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            session_id: Optional session UUID
        """
        from app.models.audit_log import AuditLog

        # Create database record if db session provided
        if db is not None:
            audit_log = AuditLog(
                user_id=user_id,
                action="login_success",
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                event_metadata={
                    "email": email,
                    "session_id": str(session_id) if session_id else None,
                },
            )
            db.add(audit_log)
            await db.commit()

        # Also log to structured logger for redundancy
        logger.info(
            "User login successful",
            extra={
                "event_type": AuditEventType.LOGIN_SUCCESS.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": str(session_id) if session_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_login_failed(
        db: AsyncSession,
        email: str,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log failed login attempt to database and logger.

        Args:
            db: Database session for persisting audit log
            email: Email address used in attempt
            reason: Reason for failure (e.g., "invalid_credentials", "email_not_verified")
            ip_address: Optional client IP address
            user_agent: Optional client user agent
        """
        from app.models.audit_log import AuditLog

        # Create database record (user_id is NULL for failed attempts)
        audit_log = AuditLog(
            user_id=None,  # NULL for failed login attempts
            action="login_failed",
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            event_metadata={
                "email": email,
                "reason": reason,
            },
        )
        db.add(audit_log)
        await db.commit()

        # Also log to structured logger
        logger.warning(
            "User login failed",
            extra={
                "event_type": AuditEventType.LOGIN_FAILED.value,
                "email": email,
                "reason": reason,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    @staticmethod
    async def log_logout(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
        session_id: uuid.UUID | None = None,
    ) -> None:
        """Log user logout event to database and logger.

        Args:
            db: Database session for persisting audit log
            user_id: UUID of user logging out
            email: User's email address
            ip_address: Optional client IP address
            session_id: Optional session UUID being terminated
        """
        from app.models.audit_log import AuditLog

        # Create database record
        audit_log = AuditLog(
            user_id=user_id,
            action="logout",
            ip_address=ip_address or "unknown",
            user_agent=None,
            event_metadata={
                "email": email,
                "session_id": str(session_id) if session_id else None,
            },
        )
        db.add(audit_log)
        await db.commit()

        # Also log to structured logger
        logger.info(
            "User logout",
            extra={
                "event_type": AuditEventType.LOGOUT.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "session_id": str(session_id) if session_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_session_revoked(
        user_id: uuid.UUID,
        email: str,
        session_jti: str,
        reason: str | None = None,
        ip_address: str | None = None,
        revoked_by_user_id: uuid.UUID | None = None,
    ) -> None:
        """Log session revocation event.

        Args:
            user_id: UUID of user whose session was revoked
            email: User's email address
            session_jti: JWT ID of the revoked session
            reason: Optional reason for revocation (e.g., "password_reset", "security_breach", "manual_logout")
            ip_address: Optional IP address where revocation occurred
            revoked_by_user_id: Optional UUID of admin who revoked session (if different from user)
        """
        logger.warning(
            "Session revoked",
            extra={
                "event_type": AuditEventType.SESSION_REVOKED.value,
                "user_id": str(user_id),
                "email": email,
                "session_jti": session_jti,
                "reason": reason,
                "ip_address": ip_address,
                "revoked_by_user_id": str(revoked_by_user_id) if revoked_by_user_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_account_created(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log new account creation.

        Args:
            user_id: UUID of newly created user
            email: User's email address
            ip_address: Optional client IP address
        """
        logger.info(
            "User account created",
            extra={
                "event_type": AuditEventType.ACCOUNT_CREATED.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_password_reset_request(
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log password reset request.

        Args:
            email: Email address requesting reset
            ip_address: Optional client IP address
        """
        logger.info(
            "Password reset requested",
            extra={
                "event_type": AuditEventType.PASSWORD_RESET_REQUEST.value,
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_password_reset_complete(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log successful password reset completion.

        Args:
            user_id: UUID of user whose password was reset
            email: User's email address
            ip_address: Optional client IP address
        """
        logger.info(
            "Password reset completed",
            extra={
                "event_type": AuditEventType.PASSWORD_RESET_COMPLETE.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_password_changed(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log password change by authenticated user to database and logger.

        Args:
            db: Database session for persisting audit log
            user_id: UUID of user who changed their password
            email: User's email address
            ip_address: Optional client IP address
        """
        from app.models.audit_log import AuditLog

        # Create database record
        audit_log = AuditLog(
            user_id=user_id,
            action="password_changed",
            ip_address=ip_address or "unknown",
            user_agent=None,
            event_metadata={"email": email},
        )
        db.add(audit_log)
        await db.commit()

        # Also log to structured logger
        logger.info(
            "Password changed",
            extra={
                "event_type": AuditEventType.PASSWORD_CHANGED.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_email_verification(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log email verification completion to database and logger.

        Args:
            db: Database session for persisting audit log
            user_id: UUID of user whose email was verified
            email: Email address that was verified
            ip_address: Optional client IP address
        """
        from app.models.audit_log import AuditLog

        # Create database record
        audit_log = AuditLog(
            user_id=user_id,
            action="email_verified",
            ip_address=ip_address or "unknown",
            user_agent=None,
            event_metadata={"email": email},
        )
        db.add(audit_log)
        await db.commit()

        # Also log to structured logger
        logger.info(
            "Email verified",
            extra={
                "event_type": AuditEventType.EMAIL_VERIFICATION.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_token_refreshed(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log access token refresh.

        Args:
            user_id: UUID of user refreshing token
            email: User's email address
            ip_address: Optional client IP address
        """
        logger.info(
            "Access token refreshed",
            extra={
                "event_type": AuditEventType.TOKEN_REFRESHED.value,
                "user_id": str(user_id),
                "email": email,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_unauthorized_access_attempt(
        resource: str,
        reason: str,
        ip_address: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> None:
        """Log unauthorized access attempt.

        Args:
            resource: Resource being accessed
            reason: Reason for denial (e.g., "invalid_token", "insufficient_permissions")
            ip_address: Optional client IP address
            user_id: Optional UUID if user was partially authenticated
        """
        logger.warning(
            "Unauthorized access attempt",
            extra={
                "event_type": AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT.value,
                "resource": resource,
                "reason": reason,
                "ip_address": ip_address,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_account_deactivated(
        user_id: uuid.UUID,
        email: str,
        reason: str | None = None,
        admin_user_id: uuid.UUID | None = None,
    ) -> None:
        """Log account deactivation.

        Args:
            user_id: UUID of deactivated user
            email: User's email address
            reason: Optional reason for deactivation
            admin_user_id: Optional UUID of admin who deactivated account
        """
        logger.warning(
            "User account deactivated",
            extra={
                "event_type": AuditEventType.ACCOUNT_DEACTIVATED.value,
                "user_id": str(user_id),
                "email": email,
                "reason": reason,
                "admin_user_id": str(admin_user_id) if admin_user_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_role_changed(
        user_id: uuid.UUID,
        email: str,
        old_role: str,
        new_role: str,
        admin_user_id: uuid.UUID,
        admin_email: str,
    ) -> None:
        """Log role change event.

        Args:
            user_id: UUID of user whose role changed
            email: User's email address
            old_role: Previous role name
            new_role: New role name
            admin_user_id: UUID of admin who changed the role
            admin_email: Email of admin who changed the role
        """
        logger.info(
            "User role changed",
            extra={
                "event_type": AuditEventType.ROLE_CHANGED.value,
                "user_id": str(user_id),
                "email": email,
                "old_role": old_role,
                "new_role": new_role,
                "admin_user_id": str(admin_user_id),
                "admin_email": admin_email,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_user_created(
        user_id: uuid.UUID,
        email: str,
        role: str,
        admin_user_id: uuid.UUID,
        admin_email: str,
    ) -> None:
        """Log user creation event.

        Args:
            user_id: UUID of created user
            email: New user's email address
            role: Assigned role name
            admin_user_id: UUID of admin who created the user
            admin_email: Email of admin who created the user
        """
        logger.info(
            "User created by admin",
            extra={
                "event_type": AuditEventType.USER_CREATED.value,
                "user_id": str(user_id),
                "email": email,
                "role": role,
                "admin_user_id": str(admin_user_id),
                "admin_email": admin_email,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_user_updated(
        user_id: uuid.UUID,
        email: str,
        fields_updated: list[str],
        admin_user_id: uuid.UUID,
        admin_email: str,
    ) -> None:
        """Log user profile update event.

        Args:
            user_id: UUID of updated user
            email: User's email address
            fields_updated: List of field names that were updated
            admin_user_id: UUID of admin who updated the user
            admin_email: Email of admin who updated the user
        """
        logger.info(
            "User profile updated",
            extra={
                "event_type": AuditEventType.USER_UPDATED.value,
                "user_id": str(user_id),
                "email": email,
                "fields_updated": fields_updated,
                "admin_user_id": str(admin_user_id),
                "admin_email": admin_email,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_user_deleted(
        user_id: uuid.UUID,
        email: str,
        admin_user_id: uuid.UUID,
        admin_email: str,
    ) -> None:
        """Log user deletion/deactivation event.

        Args:
            user_id: UUID of deleted user
            email: User's email address
            admin_user_id: UUID of admin who deleted the user
            admin_email: Email of admin who deleted the user
        """
        logger.warning(
            "User deleted/deactivated",
            extra={
                "event_type": AuditEventType.USER_DELETED.value,
                "user_id": str(user_id),
                "email": email,
                "admin_user_id": str(admin_user_id),
                "admin_email": admin_email,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_account_reactivated(
        user_id: uuid.UUID,
        email: str,
        admin_user_id: uuid.UUID | None = None,
    ) -> None:
        """Log account reactivation.

        Args:
            user_id: UUID of reactivated user
            email: User's email address
            admin_user_id: Optional UUID of admin who reactivated account
        """
        logger.info(
            "User account reactivated",
            extra={
                "event_type": AuditEventType.ACCOUNT_REACTIVATED.value,
                "user_id": str(user_id),
                "email": email,
                "admin_user_id": str(admin_user_id) if admin_user_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
