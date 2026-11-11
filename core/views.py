from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def live_health(request):
    # Liveness reports process availability only and intentionally avoids a
    # database dependency so an orchestrator can restart unhealthy workers.
    return JsonResponse({"status": "ok", "service": "student-record-system", "time": timezone.now().isoformat()})


def ready_health(request):
    try:
        # Readiness performs a minimal database round trip before accepting
        # traffic, keeping dependency failures visible to the service monitor.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ready", "database": "ok"})
    except Exception:
        return JsonResponse({"status": "not-ready", "database": "unavailable"}, status=503)
