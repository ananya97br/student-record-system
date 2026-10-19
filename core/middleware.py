from __future__ import annotations

import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from .auth import decode_token

logger = logging.getLogger("srs")


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))[:100]
        response = self.get_response(request)
        response["X-Correlation-ID"] = request.correlation_id
        return response


class JwtCookieMiddleware:
    """Attach the user represented by the signed HttpOnly JWT cookie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = AnonymousUser()
        token = request.COOKIES.get(settings.JWT_COOKIE_NAME)
        if token:
            try:
                payload = decode_token(token)
                from accounts.models import User

                user = User.objects.get(pk=payload["sub"], status=User.Status.ACTIVE)
                if user.token_version == payload.get("ver"):
                    request.user = user
            except Exception:
                logger.info("invalid authentication cookie", extra={"correlation_id": getattr(request, "correlation_id", "unknown")})
        return self.get_response(request)


def csrf_valid(request) -> bool:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return True
    supplied = request.headers.get("X-CSRFToken", "")
    cookie = request.COOKIES.get("csrftoken", "")
    return bool(supplied and cookie and supplied == cookie)
