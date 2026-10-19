from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def live_health(request):
    return JsonResponse({"status": "ok", "service": "student-record-system", "time": timezone.now().isoformat()})


def ready_health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ready", "database": "ok"})
    except Exception:
        return JsonResponse({"status": "not-ready", "database": "unavailable"}, status=503)
