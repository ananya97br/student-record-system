from __future__ import annotations

from functools import wraps

from .audit import audit
from .errors import error_response
from .middleware import csrf_valid


def api_view(require_csrf: bool = True):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if require_csrf and not csrf_valid(request):
                return error_response("CSRF_REQUIRED", "A valid CSRF header is required.", getattr(request, "correlation_id", "unknown"), 403)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not getattr(request.user, "is_authenticated", False):
            return error_response("AUTHENTICATION_REQUIRED", "Authentication is required.", getattr(request, "correlation_id", "unknown"), 401)
        return view(request, *args, **kwargs)

    return wrapped


def roles(*allowed):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in allowed:
                audit(request, "AUTHORIZATION_DENIED", "Endpoint", request.path, {"requiredRoles": allowed})
                return error_response("FORBIDDEN", "You are not authorized for this action.", request.correlation_id, 403)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def parse_json(request):
    import json

    try:
        return json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return None
