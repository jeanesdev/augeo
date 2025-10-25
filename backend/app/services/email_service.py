"""Email service using Azure Communication Services.

T057: Azure Communication Services email client for sending password reset emails
T159: Error handling and retry logic for email service failures
"""

import asyncio
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailServiceError(Exception):
    """Base exception for email service errors."""

    pass


class EmailSendError(EmailServiceError):
    """Exception raised when email sending fails."""

    pass


class EmailService:
    """Email service for sending transactional emails via Azure Communication Services."""

    def __init__(self) -> None:
        """Initialize email service."""
        # TODO: Initialize Azure Communication Services client when credentials are configured
        # For now, log emails to console for development
        self.enabled = False  # Set to True when Azure credentials are configured
        logger.info("EmailService initialized (mock mode for development)")

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str | None = None
    ) -> bool:
        """
        Send password reset email with reset link and retry logic.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: Optional user's first name for personalization

        Returns:
            True if email sent successfully, False otherwise

        Raises:
            EmailSendError: If email fails to send after all retries
        """
        # Construct reset link (admin portal)
        reset_url = f"{settings.frontend_admin_url}/reset-password?token={reset_token}"

        # Email content
        subject = "Reset Your Password - Augeo Platform"
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        body = f"""
{greeting}

You requested to reset your password for your Augeo Platform account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.

Best regards,
The Augeo Platform Team
        """.strip()

        # Send with retry logic
        return await self._send_email_with_retry(to_email, subject, body, "password_reset")

    async def send_verification_email(
        self, to_email: str, verification_token: str, user_name: str | None = None
    ) -> bool:
        """
        Send email verification email with retry logic.

        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            user_name: Optional user's first name for personalization

        Returns:
            True if email sent successfully, False otherwise

        Raises:
            EmailSendError: If email fails to send after all retries
        """
        # Construct verification link (admin portal)
        verification_url = f"{settings.frontend_admin_url}/verify-email?token={verification_token}"

        # Email content
        subject = "Verify Your Email - Augeo Platform"
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        body = f"""
{greeting}

Welcome to Augeo Platform!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Augeo Platform Team
        """.strip()

        # Send with retry logic
        return await self._send_email_with_retry(to_email, subject, body, "verification")

    async def _send_email_with_retry(
        self, to_email: str, subject: str, body: str, email_type: str
    ) -> bool:
        """
        Send email with retry logic and error handling.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            email_type: Type of email (for logging)

        Returns:
            True if email sent successfully

        Raises:
            EmailSendError: If email fails after all retries
        """
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # TODO: Send via Azure Communication Services when configured
                if self.enabled:
                    # When Azure credentials are configured:
                    # await self._send_via_azure(to_email, subject, body)
                    pass
                else:
                    # Mock mode for development
                    logger.info(
                        f"[MOCK EMAIL] {email_type} email\n"
                        f"To: {to_email}\n"
                        f"Subject: {subject}\n"
                        f"Body:\n{body}"
                    )
                return True

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Email sending failed, retrying",
                        extra={
                            "email_type": email_type,
                            "to_email": to_email,
                            "error": str(e),
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                        },
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        "Email sending failed after all retries",
                        extra={
                            "email_type": email_type,
                            "to_email": to_email,
                            "error": str(e),
                            "max_retries": max_retries,
                        },
                    )
                    raise EmailSendError(
                        f"Failed to send {email_type} email after {max_retries} attempts"
                    ) from e

        return False  # Should not reach here

    async def _send_via_azure(self, to_email: str, subject: str, body: str) -> None:
        """
        Send email via Azure Communication Services.

        TODO: Implement when Azure credentials are configured
        Requires:
        - AZURE_COMMUNICATION_CONNECTION_STRING in settings
        - Azure Communication Services Email resource

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
        """
        # from azure.communication.email import EmailClient
        # client = EmailClient.from_connection_string(
        #     settings.azure_communication_connection_string
        # )
        # message = {
        #     "senderAddress": settings.email_from_address,
        #     "recipients": {"to": [{"address": to_email}]},
        #     "content": {
        #         "subject": subject,
        #         "plainText": body,
        #     },
        # }
        # poller = await client.begin_send(message)
        # await poller.result()
        pass


# Singleton instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
