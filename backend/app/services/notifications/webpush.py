"""Web Push notification service using pywebpush + VAPID."""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("sahulat.notifications.webpush")


@dataclass
class NotificationResult:
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


@dataclass
class BatchResult:
    results: list[NotificationResult]

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


class WebPushService:
    """Web Push notification service using pywebpush with VAPID."""

    def __init__(self):
        self.vapid_public_key = settings.vapid_public_key
        self.vapid_private_key = settings.vapid_private_key
        self.vapid_email = settings.vapid_email

    def send_notification(
        self,
        subscription: dict,
        payload: dict,
        ttl: int = 3600,
    ) -> NotificationResult:
        """Send a Web Push notification to a single subscription.

        Handles expired/invalid subscriptions gracefully (404/410).
        """
        try:
            from pywebpush import webpush, WebPushException

            response = webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}" if self.vapid_email else "mailto:admin@sahulat.pk",
                    "aud": "https://sahulat.pk",
                },
                ttl=ttl,
            )
            return NotificationResult(success=True, status_code=response.status_code)

        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                logger.info("Push subscription expired/gone: %s", e)
                return NotificationResult(success=False, status_code=e.response.status_code, error=str(e))
            logger.warning("Web Push failed: %s", e)
            return NotificationResult(success=False, error=str(e))
        except Exception as e:
            logger.error("Unexpected Web Push error: %s", e)
            return NotificationResult(success=False, error=str(e))

    def send_batch(
        self,
        subscriptions: list[dict],
        payload: dict,
    ) -> BatchResult:
        """Send to multiple subscriptions; handle failures individually."""
        results = []
        for sub in subscriptions:
            result = self.send_notification(sub, payload)
            results.append(result)
        return BatchResult(results=results)

    @staticmethod
    def is_configured() -> bool:
        """Check if VAPID keys are configured."""
        return bool(settings.vapid_private_key) and bool(settings.vapid_public_key)


push_service = WebPushService()
