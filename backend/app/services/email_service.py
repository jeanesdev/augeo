"""Email service using Azure Communication Services.

T057: Azure Communication Services email client for sending password reset emails
T159: Error handling and retry logic for email service failures
"""

import asyncio
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import EMAIL_FAILURES_TOTAL

logger = get_logger(__name__)
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
        # Enable Azure Communication Services if connection string is configured
        self.enabled = settings.azure_communication_connection_string is not None
        if self.enabled:
            logger.info("EmailService initialized (Azure Communication Services enabled)")
        else:
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

        # HTML email body
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Password Reset</h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.5;">
                                {greeting}
                            </p>
                            <p style="margin: 0 0 30px; color: #666666; font-size: 16px; line-height: 1.5;">
                                We received a request to reset your password for your Augeo Platform account. Click the button below to create a new password.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(240, 147, 251, 0.4);">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alternative link -->
                            <p style="margin: 30px 0 0; color: #999999; font-size: 14px; line-height: 1.5; text-align: center;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{reset_url}" style="color: #f093fb; text-decoration: none; word-break: break-all;">{reset_url}</a>
                            </p>

                            <!-- Expiry notice -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-top: 30px;">
                                <tr>
                                    <td style="padding: 20px; background-color: #fff3cd; border-radius: 6px; border-left: 4px solid #ffc107;">
                                        <p style="margin: 0; color: #856404; font-size: 14px; line-height: 1.5;">
                                            <strong>⏰ Important:</strong> This password reset link will expire in 1 hour for security purposes.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 0; color: #999999; font-size: 14px; line-height: 1.5;">
                                If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center; background-color: #f8f9fa; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px; color: #666666; font-size: 14px;">
                                Best regards,<br>
                                <strong>The Augeo Platform Team</strong>
                            </p>
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © 2025 Augeo Platform. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """.strip()

        # Plain text fallback
        plain_text_body = f"""
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
        return await self._send_email_with_retry(
            to_email, subject, html_body, plain_text_body, "password_reset"
        )

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

        # HTML email body
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Welcome to Augeo!</h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.5;">
                                {greeting}
                            </p>
                            <p style="margin: 0 0 30px; color: #666666; font-size: 16px; line-height: 1.5;">
                                Thank you for joining Augeo Platform! We're excited to have you on board. To get started, please verify your email address by clicking the button below.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.4);">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alternative link -->
                            <p style="margin: 30px 0 0; color: #999999; font-size: 14px; line-height: 1.5; text-align: center;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{verification_url}" style="color: #667eea; text-decoration: none; word-break: break-all;">{verification_url}</a>
                            </p>

                            <!-- Expiry notice -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-top: 30px;">
                                <tr>
                                    <td style="padding: 20px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #667eea;">
                                        <p style="margin: 0; color: #666666; font-size: 14px; line-height: 1.5;">
                                            <strong>⏰ Important:</strong> This verification link will expire in 24 hours for security purposes.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 0; color: #999999; font-size: 14px; line-height: 1.5;">
                                If you didn't create an account with Augeo, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center; background-color: #f8f9fa; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px; color: #666666; font-size: 14px;">
                                Best regards,<br>
                                <strong>The Augeo Platform Team</strong>
                            </p>
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © 2025 Augeo Platform. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """.strip()

        # Plain text fallback for email clients that don't support HTML
        plain_text_body = f"""
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
        return await self._send_email_with_retry(
            to_email, subject, html_body, plain_text_body, "verification"
        )

    async def _send_email_with_retry(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_text_body: str | None = None,
        email_type: str = "email",
    ) -> bool:
        """
        Send email with retry logic and error handling.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: Email body (HTML)
            plain_text_body: Email body (plain text fallback)
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
                if self.enabled:
                    # Send via Azure Communication Services
                    await self._send_via_azure(to_email, subject, html_body, plain_text_body)
                    logger.info(
                        "Email sent successfully",
                        extra={
                            "email_type": email_type,
                            "to_email": to_email,
                        },
                    )
                else:
                    # Mock mode for development
                    display_body = plain_text_body if plain_text_body else html_body[:200]
                    logger.info(
                        f"[MOCK EMAIL] {email_type} email\n"
                        f"To: {to_email}\n"
                        f"Subject: {subject}\n"
                        f"Body:\n{display_body}"
                    )
                return True

            except Exception as e:
                # Increment failure counter
                EMAIL_FAILURES_TOTAL.inc()

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

    async def _send_via_azure(
        self, to_email: str, subject: str, html_body: str, plain_text_body: str | None = None
    ) -> None:
        """
        Send email via Azure Communication Services.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: Email body (HTML)
            plain_text_body: Email body (plain text fallback)

        Raises:
            Exception: If email sending fails
        """
        from concurrent.futures import ThreadPoolExecutor

        from azure.communication.email import EmailClient

        if not settings.azure_communication_connection_string:
            raise EmailServiceError("Azure Communication Services connection string not configured")

        logger.info(f"Sending email via Azure to {to_email}")

        try:
            # Create email client
            client = EmailClient.from_connection_string(
                settings.azure_communication_connection_string
            )

            # Construct message with HTML and plain text
            content = {"subject": subject, "html": html_body}
            if plain_text_body:
                content["plainText"] = plain_text_body

            message = {
                "senderAddress": settings.email_from_address,
                "recipients": {"to": [{"address": to_email}]},
                "content": content,
            }

            logger.info("Message constructed, beginning send operation")

            # Azure SDK is synchronous - run in thread pool to avoid blocking
            def _send_sync() -> dict[str, Any]:
                logger.info("Starting synchronous send operation")
                poller = client.begin_send(message)
                logger.info("Got poller, waiting for result")
                result = poller.result()
                logger.info(
                    f"Send operation completed with status: {result.get('status', 'unknown')}"
                )
                return dict(result)  # Cast to dict for type safety

            # Run synchronous operation in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, _send_sync)

            # Check if email was queued successfully
            if result.get("status") != "Succeeded":
                raise EmailSendError(
                    f"Email send failed with status: {result.get('status', 'unknown')}"
                )

            logger.info(f"Email successfully queued for {to_email}")

        except Exception as e:
            logger.error(f"Error sending email via Azure: {str(e)}", exc_info=True)
            raise


# Singleton instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
