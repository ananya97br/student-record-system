from __future__ import annotations

from rest_framework.views import exception_handler


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, field_errors: dict | None = None):
        self.code = code
        self.message = message
        self.status = status
        self.field_errors = field_errors or {}
        super().__init__(message)


def error_response(code: str, message: str, correlation_id: str, status: int = 400, field_errors: dict | None = None):
    from django.http import JsonResponse

    return JsonResponse({"code": code, "message": message, "correlationId": correlation_id, "fieldErrors": field_errors or {}}, status=status)


def drf_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    request = context.get("request")
    correlation_id = getattr(request, "correlation_id", "unknown")
    detail = response.data.get("detail", "Request failed") if isinstance(response.data, dict) else "Request failed"
    field_errors = response.data if isinstance(response.data, dict) and "detail" not in response.data else {}
    response.data = {"code": "REQUEST_ERROR", "message": str(detail), "correlationId": correlation_id, "fieldErrors": field_errors}
    return response
