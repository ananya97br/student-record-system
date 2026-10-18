from __future__ import annotations

import subprocess

from django.conf import settings


class MalwareScanner:
    def scan(self, content: bytes) -> str:
        raise NotImplementedError


class DeterministicScanner(MalwareScanner):
    """Local scanner that detects the standard EICAR test string."""

    def scan(self, content: bytes) -> str:
        return "INFECTED" if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content else "CLEAN"


class ClamAVScanner(MalwareScanner):
    """Optional adapter for a local clamdscan binary/container."""

    def scan(self, content: bytes) -> str:
        result = subprocess.run(["clamdscan", "--fdpass", "--no-summary", "-"], input=content, capture_output=True, timeout=30, check=False)
        return "CLEAN" if result.returncode == 0 else "INFECTED"


def get_scanner() -> MalwareScanner:
    if getattr(settings, "MALWARE_SCANNER", "deterministic").lower() == "clamav":
        return ClamAVScanner()
    return DeterministicScanner()
