from __future__ import annotations

from datetime import timedelta
import jwt
from django.conf import settings
from django.utils import timezone


def issue_token(user) -> str:
    now = timezone.now()
    return jwt.encode(
        {"sub": str(user.pk), "role": user.role, "ver": user.token_version, "iat": now, "exp": now + timedelta(minutes=settings.JWT_TTL_MINUTES)},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
