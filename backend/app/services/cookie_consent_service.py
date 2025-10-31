"""Cookie consent service for EU Cookie Law compliance.

This service provides methods for managing user cookie preferences
for both authenticated and anonymous users.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentAction, ConsentAuditLog, CookieConsent
from app.models.user import User
from app.schemas.cookies import (
    CookieConsentRequest,
    CookieConsentResponse,
    CookieConsentStatusResponse,
    CookieConsentUpdateRequest,
)


class CookieConsentService:
    """Service for cookie consent management operations."""

    async def get_cookie_consent(
        self,
        db: AsyncSession,
        user: User | None = None,
        session_id: str | None = None,
    ) -> CookieConsentStatusResponse:
        """Get cookie consent status for user or session.

        Args:
            db: Database session
            user: Authenticated user (optional)
            session_id: Anonymous session ID (optional)

        Returns:
            Cookie consent status

        Raises:
            ValueError: If neither user nor session_id provided
        """
        if not user and not session_id:
            raise ValueError("Either user or session_id must be provided")

        # Query for consent
        if user:
            stmt = select(CookieConsent).where(CookieConsent.user_id == user.id)
        else:
            stmt = select(CookieConsent).where(CookieConsent.session_id == session_id)

        stmt = stmt.order_by(CookieConsent.created_at.desc()).limit(1)

        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            # No consent recorded - return defaults (reject all non-essential)
            return CookieConsentStatusResponse(
                essential=True,
                analytics=False,
                marketing=False,
                has_consent=False,
            )

        return CookieConsentStatusResponse(
            essential=consent.essential,
            analytics=consent.analytics,
            marketing=consent.marketing,
            has_consent=True,
        )

    async def set_cookie_consent(
        self,
        db: AsyncSession,
        request: CookieConsentRequest,
        ip_address: str,
        user_agent: str | None,
        user: User | None = None,
        session_id: str | None = None,
    ) -> CookieConsentResponse:
        """Set cookie consent preferences.

        Args:
            db: Database session
            request: Cookie consent request
            ip_address: User's IP address
            user_agent: User's user agent
            user: Authenticated user (optional)
            session_id: Anonymous session ID (optional)

        Returns:
            Created cookie consent

        Raises:
            ValueError: If neither user nor session_id provided
        """
        if not user and not session_id:
            raise ValueError("Either user or session_id must be provided")

        # Create consent record
        consent = CookieConsent(
            user_id=user.id if user else None,
            session_id=session_id,
            essential=True,  # Always true
            analytics=request.analytics,
            marketing=request.marketing,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(consent)

        # Log to audit trail (only for authenticated users)
        if user:
            audit_log = ConsentAuditLog(
                user_id=user.id,
                action=ConsentAction.COOKIE_CONSENT_UPDATED,
                details={
                    "analytics": request.analytics,
                    "marketing": request.marketing,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_log)

        await db.commit()
        await db.refresh(consent)

        return CookieConsentResponse.model_validate(consent)

    async def update_cookie_consent(
        self,
        db: AsyncSession,
        request: CookieConsentUpdateRequest,
        ip_address: str,
        user_agent: str | None,
        user: User | None = None,
        session_id: str | None = None,
    ) -> CookieConsentResponse:
        """Update existing cookie consent preferences.

        Args:
            db: Database session
            request: Cookie consent update request
            ip_address: User's IP address
            user_agent: User's user agent
            user: Authenticated user (optional)
            session_id: Anonymous session ID (optional)

        Returns:
            Updated cookie consent

        Raises:
            ValueError: If neither user nor session_id provided or no consent found
        """
        if not user and not session_id:
            raise ValueError("Either user or session_id must be provided")

        # Find existing consent
        if user:
            stmt = select(CookieConsent).where(CookieConsent.user_id == user.id)
        else:
            stmt = select(CookieConsent).where(CookieConsent.session_id == session_id)

        stmt = stmt.order_by(CookieConsent.created_at.desc()).limit(1)

        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            # No existing consent - create new one
            return await self.set_cookie_consent(
                db=db,
                request=CookieConsentRequest(
                    analytics=request.analytics,
                    marketing=request.marketing,
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                user=user,
                session_id=session_id,
            )

        # Update preferences
        consent.analytics = request.analytics
        consent.marketing = request.marketing

        # Log to audit trail (only for authenticated users)
        if user:
            audit_log = ConsentAuditLog(
                user_id=user.id,
                action=ConsentAction.COOKIE_CONSENT_UPDATED,
                details={
                    "analytics": request.analytics,
                    "marketing": request.marketing,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_log)

        await db.commit()
        await db.refresh(consent)

        return CookieConsentResponse.model_validate(consent)

    async def revoke_cookie_consent(
        self,
        db: AsyncSession,
        ip_address: str,
        user_agent: str | None,
        user: User | None = None,
        session_id: str | None = None,
    ) -> CookieConsentResponse:
        """Revoke cookie consent (set all to false except essential).

        Args:
            db: Database session
            ip_address: User's IP address
            user_agent: User's user agent
            user: Authenticated user (optional)
            session_id: Anonymous session ID (optional)

        Returns:
            Updated cookie consent
        """
        return await self.update_cookie_consent(
            db=db,
            request=CookieConsentUpdateRequest(
                analytics=False,
                marketing=False,
            ),
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
            session_id=session_id,
        )
