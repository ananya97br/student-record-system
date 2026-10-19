from __future__ import annotations

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger("srs")


def notify(user, subject: str, body: str, channel: str = "EMAIL", safe_metadata: dict | None = None) -> bool:
    from accounts.models import Notification

    notification = Notification.objects.create(recipient=user, channel=channel, subject=subject, body=body, metadata=safe_metadata or {})
    try:
        if channel == "EMAIL" and user.email:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        notification.status = "SENT"
        notification.delivered_at = timezone.now()
        notification.save(update_fields=["status", "delivered_at"])
        return True
    except Exception as exc:
        notification.status = "FAILED"
        notification.attempts += 1
        notification.last_error = str(exc)[:500]
        notification.save(update_fields=["status", "attempts", "last_error"])
        logger.warning("notification delivery failed", extra={"module": "notifications", "user_id": str(user.pk)})
        return False
