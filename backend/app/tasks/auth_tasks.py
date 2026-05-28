"""
CodeGuard AI - Authentication Background Tasks
Celery tasks for async auth operations like password reset emails.
"""

from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="send_password_reset_email", bind=True, max_retries=3)
def send_password_reset_email_task(self, to_email: str, to_name: str, reset_token: str):
    """Celery task to send a password reset email.

    This runs asynchronously via Celery when Redis is available.
    Falls back to synchronous sending when Celery is not configured.
    """
    import asyncio
    from app.services.email_service import email_service

    try:
        # Run async email sending via asyncio.run() which handles
        # loop creation and cleanup properly (Python 3.10+)
        result = asyncio.run(
            email_service.send_password_reset_email(
                to_email=to_email,
                to_name=to_name,
                reset_token=reset_token,
            )
        )

        logger.info(f"Password reset email sent to {to_email}")
        return result
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {to_email}: {exc}")
        raise self.retry(exc=exc, countdown=60)