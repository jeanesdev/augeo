"""Audit logging service for security events.

Logs authentication and authorization events for compliance and security monitoring.
"""

import uuid
from datetime import datetime
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events to log."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_REACTIVATED = "account_reactivated"
    TOKEN_REFRESHED = "token_refreshed"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"


class AuditService:
    """Service for logging security and authentication audit events.

    Uses structured logging to capture security events with full context.
    In production, these logs should be sent to a SIEM or log aggregation service.
    """

    @staticmethod
    def log_login_success(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: uuid.UUID | None = None,
    ) -> None:
        """Log successful login event.

        Args:
            user_id: UUID of authenticated user
            email: User's email address
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            session_id: Optional session UUID
        """
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
    def log_login_failed(
        email: str,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log failed login attempt.

        Args:
            email: Email address used in attempt
            reason: Reason for failure (e.g., "invalid_credentials", "email_not_verified")
            ip_address: Optional client IP address
            user_agent: Optional client user agent
        """
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
    def log_logout(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
        session_id: uuid.UUID | None = None,
    ) -> None:
        """Log user logout event.

        Args:
            user_id: UUID of user logging out
            email: User's email address
            ip_address: Optional client IP address
            session_id: Optional session UUID being terminated
        """
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
    def log_email_verification(
        user_id: uuid.UUID,
        email: str,
        ip_address: str | None = None,
    ) -> None:
        """Log email verification completion.

        Args:
            user_id: UUID of user whose email was verified
            email: Email address that was verified
            ip_address: Optional client IP address
        """
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
