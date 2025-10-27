"""Session service for managing user sessions (PostgreSQL audit + Redis active tracking)."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.services.audit_service import AuditService
from app.services.redis_service import RedisService


class SessionService:
    """Service for managing user sessions.

    Implements hybrid storage:
    - PostgreSQL: Immutable audit trail (write-only)
    - Redis: Active session validation (source of truth)
    """

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        refresh_token_jti: str,
        device_info: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """Create new session in PostgreSQL and Redis.

        Args:
            db: Database session
            user_id: User UUID
            refresh_token_jti: JWT ID from refresh token
            device_info: Optional device information
            ip_address: Optional IP address
            user_agent: Optional user agent string

        Returns:
            Created Session model
        """
        # Calculate expiry (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create session record in PostgreSQL (audit trail)
        session = Session(
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            device_info=device_info,
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            expires_at=expires_at,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Store in Redis (active session tracking)
        await RedisService.set_session(
            user_id=user_id,
            jti=refresh_token_jti,
            device_info=device_info,
            ip_address=ip_address,
        )

        return session

    @staticmethod
    async def get_active_session(
        user_id: uuid.UUID,
        refresh_token_jti: str,
    ) -> dict[str, Any] | None:
        """Check if session is active in Redis.

        PostgreSQL is NOT queried - Redis is source of truth for active sessions.

        Args:
            user_id: User UUID
            refresh_token_jti: JWT ID from refresh token

        Returns:
            Session data dict if active, None otherwise
        """
        return await RedisService.get_session(user_id, refresh_token_jti)

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        refresh_token_jti: str,
        reason: str | None = None,
    ) -> bool:
        """Revoke session (soft delete in PostgreSQL, hard delete in Redis).

        Args:
            db: Database session
            user_id: User UUID
            refresh_token_jti: JWT ID from refresh token
            reason: Optional reason for revocation

        Returns:
            True if session was revoked, False if not found
        """
        # Fetch session details for audit logging
        stmt = select(Session).where(
            Session.user_id == user_id,
            Session.refresh_token_jti == refresh_token_jti,
            Session.revoked_at.is_(None),
        )
        session_result = await db.execute(stmt)
        session = session_result.scalar_one_or_none()

        if not session:
            return False

        # Set revoked_at in PostgreSQL (immutable audit trail)
        result = await db.execute(
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.refresh_token_jti == refresh_token_jti,
                Session.revoked_at.is_(None),  # Only revoke if not already revoked
            )
            .values(revoked_at=datetime.utcnow())
        )
        await db.commit()

        # Delete from Redis (removes active session)
        await RedisService.delete_session(user_id, refresh_token_jti)

        # Log audit event (get user email for logging)
        from app.models.user import User

        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user:
            AuditService.log_session_revoked(
                user_id=user_id,
                email=user.email,
                session_jti=refresh_token_jti,
                reason=reason or "manual_logout",
                ip_address=session.ip_address,
            )

        rows_affected: int = result.rowcount or 0  # type: ignore[attr-defined]
        return rows_affected > 0

    @staticmethod
    async def revoke_all_user_sessions(
        db: AsyncSession,
        user_id: uuid.UUID,
        except_jti: str | None = None,
        reason: str | None = None,
    ) -> int:
        """Revoke all sessions for a user (e.g., password reset, security breach).

        Args:
            db: Database session
            user_id: User UUID
            except_jti: Optional JTI to exclude (keep current session active)
            reason: Optional reason for bulk revocation

        Returns:
            Number of sessions revoked
        """
        # Get user info for audit logging
        from app.models.user import User

        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        # Build query to revoke sessions
        query = update(Session).where(
            Session.user_id == user_id,
            Session.revoked_at.is_(None),
        )

        # Exclude current session if specified
        if except_jti:
            query = query.where(Session.refresh_token_jti != except_jti)

        query = query.values(revoked_at=datetime.utcnow())

        result = await db.execute(query)
        await db.commit()

        rows_affected: int = result.rowcount or 0  # type: ignore[attr-defined]

        # Log audit event for bulk session revocation
        if user and rows_affected > 0:
            AuditService.log_session_revoked(
                user_id=user_id,
                email=user.email,
                session_jti="ALL_SESSIONS",
                reason=reason or "bulk_revocation",
            )

        # Delete from Redis (except current session)
        await RedisService.delete_all_user_sessions(user_id)

        # Re-add current session if it was excluded
        if except_jti:
            # Fetch the session to get details
            stmt = select(Session).where(
                Session.user_id == user_id,
                Session.refresh_token_jti == except_jti,
            )
            result_session = await db.execute(stmt)
            current_session = result_session.scalar_one_or_none()

            if current_session:
                await RedisService.set_session(
                    user_id=user_id,
                    jti=except_jti,
                    device_info=current_session.device_info,
                    ip_address=current_session.ip_address,
                )

        return rows_affected

    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[Session]:
        """Get all sessions for a user (for session management UI).

        Args:
            db: Database session
            user_id: User UUID
            active_only: If True, only return non-revoked sessions

        Returns:
            List of Session models
        """
        query = select(Session).where(Session.user_id == user_id)

        if active_only:
            query = query.where(Session.revoked_at.is_(None))

        query = query.order_by(Session.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
