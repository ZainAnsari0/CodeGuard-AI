"""
CodeGuard AI - Email Service
Handles sending emails via SMTP or console (for development).
"""

import html
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails. Supports console (dev) and SMTP (prod) backends."""

    async def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
    ) -> bool:
        """Send a password reset email.

        In console mode, logs the reset link.
        In SMTP mode, sends a real email.
        """
        frontend_url = settings.FRONTEND_URL
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        if settings.EMAIL_BACKEND == "console":
            logger.info("=" * 60)
            logger.info("PASSWORD RESET EMAIL (Console Mode)")
            logger.info(f"  To: {to_name}")
            logger.info(f"  From: {settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>")
            logger.info(f"  Subject: Password Reset - CodeGuard AI")
            logger.info("  Reset URL: [REDACTED — check browser]")
            logger.info("=" * 60)
            return True

        return await self._send_smtp_email(
            to_email=to_email,
            to_name=to_name,
            subject="Password Reset - CodeGuard AI",
            body=self._build_reset_email_body(reset_url, to_name),
        )

    async def _send_smtp_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> bool:
        """Send an email via SMTP."""
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = f"{to_name} <{to_email}>"

        html_part = MIMEText(body, "html")
        msg.attach(html_part)

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            logger.info("Password reset email sent")
            return True
        except Exception as e:
            logger.error("Failed to send password reset email: %s", e)
            return False

    def _build_reset_email_body(self, reset_url: str, name: str) -> str:
        """Build HTML email body for password reset."""
        safe_name = html.escape(name)
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 40px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #06b6d4; margin: 0;">CodeGuard AI</h1>
                    <p style="color: #94a3b8; margin-top: 10px;">Security Analysis Platform</p>
                </div>
                <h2 style="color: #f1f5f9;">Hello {safe_name},</h2>
                <p style="color: #cbd5e1;">We received a request to reset your password. Click the button below to set a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{html.escape(reset_url)}" style="background-color: #06b6d4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #94a3b8; font-size: 14px;">
                    This link will expire soon. If you didn't request this, you can safely ignore this email.
                </p>
                <hr style="border-color: #334155; margin: 30px 0;">
                <p style="color: #64748b; font-size: 12px;">
                    If the button above doesn't work, copy and paste this URL into your browser:<br>
                    {html.escape(reset_url)}
                </p>
            </div>
        </body>
        </html>
        """


# Singleton instance
email_service = EmailService()