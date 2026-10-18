#!/usr/bin/env python3
"""Generate ignored local secrets and the self-signed HTTPS certificate."""
from __future__ import annotations

import base64
import json
import os
import secrets
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
generated_path = ROOT / "var" / "dev-secrets.json"
generated = json.loads(generated_path.read_text()) if generated_path.exists() else {
    "django": secrets.token_urlsafe(48),
    "field": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    "lookup": secrets.token_urlsafe(32),
    "jwt": secrets.token_urlsafe(48),
    "payment": secrets.token_urlsafe(48),
}
values = {
    "DJANGO_SECRET_KEY": generated["django"],
    "FIELD_ENCRYPTION_KEY": generated["field"],
    "LOOKUP_HMAC_KEY": generated["lookup"],
    "JWT_SECRET_KEY": generated["jwt"],
    "PAYMENT_MOCK_HMAC_SECRET": generated["payment"],
}
placeholders = {
    "replace-with-a-long-random-secret",
    "replace-with-a-long-random-hmac-secret",
    "replace-with-a-long-random-jwt-secret",
    "replace-with-a-32-byte-base64-key",
    "replace-with-a-payment-hmac-secret",
}


def configure_env() -> None:
    """Create .env or repair only known placeholder secret values.

    This makes ``cp .env.example .env`` safe while preserving deliberately
    configured production values in an existing file.
    """
    if env_path.exists():
        original = env_path.read_text()
        lines = original.splitlines()
        found = set()
        for index, line in enumerate(lines):
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, current = line.split("=", 1)
            if key in values:
                found.add(key)
                if not current.strip() or current.strip() in placeholders:
                    lines[index] = f"{key}={values[key]}"
        for key, value in values.items():
            if key not in found:
                lines.append(f"{key}={value}")
        updated = "\n".join(lines) + "\n"
        if updated != original:
            env_path.write_text(updated)
            print(f"Configured placeholder secrets in {env_path}")
        else:
            print(f"Keeping configured values in {env_path}")
    else:
        template = (ROOT / ".env.example").read_text()
        for key, value in values.items():
            for placeholder in placeholders:
                template = template.replace(f"{key}={placeholder}", f"{key}={value}")
        env_path.write_text(template)
        print(f"Created {env_path}")
    try:
        env_path.chmod(0o600)
    except OSError:
        pass


configure_env()

cert_script = ROOT / "infra" / "scripts" / "generate-dev-cert.sh"
subprocess.run(["sh", str(cert_script)], check=True)
print("Bootstrap complete. Start with: docker compose up --build")
