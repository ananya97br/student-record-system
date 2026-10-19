"""Authenticated encryption and keyed lookup helpers.

Ciphertext is stored as ``v1:<nonce>:<ciphertext>`` in base64url form. The
encryption key is supplied through FIELD_ENCRYPTION_KEY; no key is in source
control. Equality lookups use a separate HMAC digest.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.db import models


def _key(value: str | bytes) -> bytes:
    raw = value.encode() if isinstance(value, str) else value
    try:
        decoded = base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4))
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return hashlib.sha256(raw).digest()


def encrypt_value(value: str) -> str:
    if value is None:
        return ""
    nonce = os.urandom(12)
    encrypted = AESGCM(_key(settings.FIELD_ENCRYPTION_KEY)).encrypt(nonce, value.encode(), None)
    return "v1:%s:%s" % (
        base64.urlsafe_b64encode(nonce).decode().rstrip("="),
        base64.urlsafe_b64encode(encrypted).decode().rstrip("="),
    )


def decrypt_value(value: str) -> str:
    if value in (None, ""):
        return ""
    try:
        version, nonce_text, encrypted_text = value.split(":", 2)
        if version != "v1":
            raise ValueError("Unsupported ciphertext version")
        nonce = base64.urlsafe_b64decode(nonce_text + "=" * (-len(nonce_text) % 4))
        encrypted = base64.urlsafe_b64decode(encrypted_text + "=" * (-len(encrypted_text) % 4))
        return AESGCM(_key(settings.FIELD_ENCRYPTION_KEY)).decrypt(nonce, encrypted, None).decode()
    except Exception as exc:
        raise ValueError("Encrypted value failed authentication") from exc


def lookup_hash(value: str) -> str:
    return hmac.new(settings.LOOKUP_HMAC_KEY.encode(), value.strip().lower().encode(), hashlib.sha256).hexdigest()


class EncryptedTextField(models.TextField):
    description = "AES-256-GCM encrypted text"

    def get_prep_value(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        text = str(value)
        return text if text.startswith("v1:") else encrypt_value(text)

    def from_db_value(self, value: Any, expression, connection) -> str:
        return decrypt_value(value) if value else ""

    def to_python(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        if isinstance(value, str) and value.startswith("v1:"):
            return decrypt_value(value)
        return str(value)


class EncryptedDecimalField(EncryptedTextField):
    def get_prep_value(self, value: Any) -> str:
        if value is None:
            return ""
        return super().get_prep_value(str(value))

    def from_db_value(self, value: Any, expression, connection):
        from decimal import Decimal

        text = super().from_db_value(value, expression, connection)
        return Decimal(text) if text else None

    def to_python(self, value: Any):
        from decimal import Decimal

        if value in (None, ""):
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(super().to_python(value))
