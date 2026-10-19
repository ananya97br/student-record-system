from __future__ import annotations


def audit(request, action: str, entity_type: str, entity_id: str | int | None, metadata: dict | None = None, actor=None):
    from accounts.models import AuditLog, SecurityAlert

    actor = actor if actor is not None else getattr(request, "user", None)
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    safe_metadata = metadata or {}
    row = AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type[:100],
        entity_id=str(entity_id) if entity_id is not None else "",
        correlation_id=getattr(request, "correlation_id", "system"),
        metadata=safe_metadata,
    )
    if action in {"AUTHORIZATION_DENIED", "REPORT_EXPORT"}:
        if action == "AUTHORIZATION_DENIED":
            SecurityAlert.objects.create(alert_type="UNAUTHORIZED_ACCESS", severity="MEDIUM", user=actor, message="An access attempt was denied.", metadata={"entity": entity_type, "id": str(entity_id)})
        else:
            from django.utils import timezone
            from datetime import timedelta

            recent = AuditLog.objects.filter(action="REPORT_EXPORT", created_at__gte=timezone.now() - timedelta(minutes=5), actor=actor).count()
            if recent >= 5:
                SecurityAlert.objects.get_or_create(alert_type="BULK_EXPORT", severity="HIGH", user=actor, resolved=False, defaults={"message": "Repeated report exports detected.", "metadata": {"count": recent}})
    return row
