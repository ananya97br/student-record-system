from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from core.models import SystemConfig

from .models import AttendanceRecord


def threshold() -> int:
    config = SystemConfig.objects.filter(key="attendance_threshold").first()
    if config:
        try:
            return int(config.value.get("value", settings.ATTENDANCE_THRESHOLD_DEFAULT))
        except (TypeError, ValueError):
            pass
    return settings.ATTENDANCE_THRESHOLD_DEFAULT


def percentage_for(student, offering):
    records = AttendanceRecord.objects.filter(student=student, session__offering=offering)
    total = records.count()
    attended = records.filter(status__in=[AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE]).count()
    percentage = round((attended / total) * 100, 2) if total else 100.0
    return {"attended": attended, "total": total, "percentage": percentage, "belowThreshold": percentage < threshold()}


def can_edit(session):
    return timezone.now() - session.session_at <= timedelta(hours=48)
