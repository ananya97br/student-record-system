from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from core.audit import audit
from core.auth import issue_token
from core.errors import error_response
from core.notifications import notify
from core.permissions import api_view, login_required, parse_json, roles

from .models import AuditLog, OtpToken, SecurityAlert, User


def _rate_limit(request, bucket: str, limit: int, window: int = 60) -> bool:
    key = f"srs-rate:{bucket}:{request.META.get('REMOTE_ADDR', 'unknown')}"
    try:
        count = cache.get(key, 0)
        if count >= limit:
            return False
        cache.set(key, count + 1, window)
    except Exception:
        pass
    return True


def _auth_response(request, user, token):
    response = JsonResponse({"user": {"id": str(user.pk), "loginId": user.login_id, "email": user.email, "role": user.role}, "csrfToken": get_token(request)})
    response.set_cookie(settings.JWT_COOKIE_NAME, token, httponly=True, secure=settings.SECURE_COOKIES, samesite="Lax", max_age=settings.JWT_TTL_MINUTES * 60, path="/")
    return response


@csrf_exempt
@api_view(require_csrf=False)
def login(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    if not _rate_limit(request, "login", 20):
        return error_response("RATE_LIMITED", "Too many login attempts. Try again later.", request.correlation_id, 429)
    data = parse_json(request)
    if not isinstance(data, dict) or not data.get("loginId") or not data.get("password"):
        return error_response("INVALID_INPUT", "loginId and password are required.", request.correlation_id, 400, {"loginId": "Required", "password": "Required"})
    login_id = str(data["loginId"]).strip()
    try:
        user = User.objects.get(login_id__iexact=login_id)
    except User.DoesNotExist:
        return error_response("INVALID_CREDENTIALS", "Invalid login ID or password.", request.correlation_id, 401)
    if user.status == User.Status.LOCKED:
        return error_response("ACCOUNT_LOCKED", "This account is locked. Contact an administrator.", request.correlation_id, 423)
    if user.status == User.Status.DISABLED or not user.is_active:
        return error_response("ACCOUNT_DISABLED", "This account is disabled.", request.correlation_id, 403)
    if not user.check_password(str(data["password"])):
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            locked.failed_login_attempts += 1
            should_lock = locked.failed_login_attempts >= settings.ACCOUNT_LOCK_FAILED_ATTEMPTS
            if should_lock:
                locked.status = User.Status.LOCKED
                locked.locked_at = timezone.now()
            locked.save(update_fields=["failed_login_attempts", "status", "locked_at", "updated_at"])
        if should_lock:
            audit(request, "ACCOUNT_LOCK", "User", user.pk, {"reason": "failed_login_threshold"})
            SecurityAlert.objects.create(alert_type="REPEATED_LOGIN_FAILURE", severity="HIGH", user=user, message="Account locked after repeated failed login attempts.", metadata={"threshold": settings.ACCOUNT_LOCK_FAILED_ATTEMPTS})
            notify(user, "Student Record System account locked", "Your account was locked after repeated unsuccessful sign-in attempts. Contact an administrator to unlock it.", safe_metadata={"reason": "failed_login_threshold"})
            return error_response("ACCOUNT_LOCKED", "This account is now locked. Contact an administrator.", request.correlation_id, 423)
        return error_response("INVALID_CREDENTIALS", "Invalid login ID or password.", request.correlation_id, 401)
    user.failed_login_attempts = 0
    user.last_login_at = timezone.now()
    user.save(update_fields=["failed_login_attempts", "last_login_at", "updated_at"])
    audit(request, "LOGIN", "User", user.pk, {"role": user.role})
    return _auth_response(request, user, issue_token(user))


@csrf_exempt
@api_view()
@login_required
def logout(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    request.user.token_version += 1
    request.user.save(update_fields=["token_version", "updated_at"])
    audit(request, "LOGOUT", "User", request.user.pk)
    response = JsonResponse({"ok": True})
    response.delete_cookie(settings.JWT_COOKIE_NAME, path="/")
    return response


@api_view(require_csrf=False)
@login_required
def me(request):
    user = request.user
    result = {"id": str(user.pk), "loginId": user.login_id, "email": user.email, "role": user.role, "status": user.status}
    if user.role == User.Role.STUDENT:
        from students.models import Student

        student = Student.objects.select_related("program").filter(user=user).first()
        if student:
            result["student"] = {"id": student.student_id, "name": student.full_name, "program": student.program.name}
    return JsonResponse({"user": result, "csrfToken": get_token(request)})


@csrf_exempt
@api_view(require_csrf=False)
def forgot_password(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    if not _rate_limit(request, "forgot-password", 5):
        return error_response("RATE_LIMITED", "Too many requests. Try again later.", request.correlation_id, 429)
    data = parse_json(request)
    if not isinstance(data, dict) or not data.get("email"):
        return error_response("INVALID_INPUT", "Email is required.", request.correlation_id, 400)
    user = User.objects.filter(email__iexact=str(data["email"]).strip(), status=User.Status.ACTIVE).first()
    if user:
        now = timezone.now()
        OtpToken.objects.filter(user=user, purpose=OtpToken.Purpose.PASSWORD_RESET, used_at__isnull=True).update(used_at=now)
        otp = f"{secrets.randbelow(1_000_000):06d}"
        digest = hashlib.sha256((otp + settings.SECRET_KEY).encode()).hexdigest()
        OtpToken.objects.create(user=user, token_hash=digest, purpose=OtpToken.Purpose.PASSWORD_RESET, expires_at=now + timedelta(minutes=settings.OTP_TTL_MINUTES))
        # The OTP is sent only through the email provider, never logged or stored in Notification.
        from django.core.mail import send_mail

        email_sent = True
        try:
            send_mail("Student Record System password reset", f"Your one-time password is {otp}. It expires in {settings.OTP_TTL_MINUTES} minutes.", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception:
            email_sent = False
        from accounts.models import Notification

        Notification.objects.create(recipient=user, channel="EMAIL", subject="Student Record System password reset", body="A password reset code was sent to the registered email address.", metadata={"purpose": "PASSWORD_RESET"}, status="SENT" if email_sent else "FAILED", attempts=1 if not email_sent else 0, last_error="Email provider unavailable" if not email_sent else "")
        audit(request, "PASSWORD_RESET_OTP_ISSUED", "User", user.pk, {"purpose": "PASSWORD_RESET"})
    return JsonResponse({"message": "If that email is registered, a one-time password has been sent."})


@csrf_exempt
@api_view(require_csrf=False)
def reset_password(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    data = parse_json(request)
    if not isinstance(data, dict) or not data.get("email") or not data.get("otp") or not data.get("newPassword"):
        return error_response("INVALID_INPUT", "email, otp, and newPassword are required.", request.correlation_id, 400)
    password = str(data["newPassword"])
    if len(password) < 10:
        return error_response("WEAK_PASSWORD", "Password must be at least 10 characters.", request.correlation_id, 400)
    user = User.objects.filter(email__iexact=str(data["email"]).strip(), status=User.Status.ACTIVE).first()
    if not user:
        return error_response("INVALID_OTP", "The one-time password is invalid or expired.", request.correlation_id, 400)
    digest = hashlib.sha256((str(data["otp"]) + settings.SECRET_KEY).encode()).hexdigest()
    token = OtpToken.objects.filter(user=user, purpose=OtpToken.Purpose.PASSWORD_RESET, token_hash=digest, used_at__isnull=True, expires_at__gt=timezone.now()).order_by("-created_at").first()
    if not token:
        return error_response("INVALID_OTP", "The one-time password is invalid or expired.", request.correlation_id, 400)
    with transaction.atomic():
        token = OtpToken.objects.select_for_update().get(pk=token.pk)
        if token.used_at or token.expires_at <= timezone.now():
            return error_response("INVALID_OTP", "The one-time password is invalid or expired.", request.correlation_id, 400)
        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])
        user.set_password(password)
        user.token_version += 1
        user.failed_login_attempts = 0
        user.save(update_fields=["password", "token_version", "failed_login_attempts", "updated_at"])
    audit(request, "PASSWORD_RESET", "User", user.pk)
    return JsonResponse({"message": "Password reset successfully."})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def unlock_user(request, user_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error_response("NOT_FOUND", "User not found.", request.correlation_id, 404)
    user.status = User.Status.ACTIVE
    user.failed_login_attempts = 0
    user.locked_at = None
    user.save(update_fields=["status", "failed_login_attempts", "locked_at", "updated_at"])
    audit(request, "ACCOUNT_UNLOCK", "User", user.pk)
    return JsonResponse({"ok": True, "userId": str(user.pk)})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def users(request):
    if request.method != "GET":
        return error_response("METHOD_NOT_ALLOWED", "GET is required.", request.correlation_id, 405)
    rows = [{"id": str(u.pk), "loginId": u.login_id, "email": u.email, "role": u.role, "status": u.status} for u in User.objects.all()[:500]]
    return JsonResponse({"items": rows, "count": len(rows)})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def update_user(request, user_id):
    if request.method != "PATCH":
        return error_response("METHOD_NOT_ALLOWED", "PATCH is required.", request.correlation_id, 405)
    data = parse_json(request)
    if not isinstance(data, dict):
        return error_response("INVALID_INPUT", "JSON object required.", request.correlation_id, 400)
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error_response("NOT_FOUND", "User not found.", request.correlation_id, 404)
    role = data.get("role")
    if role not in dict(User.Role.choices):
        return error_response("INVALID_ROLE", "Unknown role.", request.correlation_id, 400)
    if user.pk == request.user.pk and role != User.Role.SYSADMIN and request.user.role == User.Role.SYSADMIN:
        return error_response("INVALID_STATE", "A sysadmin cannot remove their own technical access.", request.correlation_id, 409)
    old = user.role
    user.role = role
    user.save(update_fields=["role", "updated_at"])
    audit(request, "ROLE_CHANGE", "User", user.pk, {"from": old, "to": role})
    return JsonResponse({"id": str(user.pk), "role": role})


@api_view(require_csrf=False)
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def security_alerts(request):
    if request.method != "GET":
        return error_response("METHOD_NOT_ALLOWED", "GET is required.", request.correlation_id, 405)
    rows = [{"id": a.id, "type": a.alert_type, "severity": a.severity, "message": a.message, "resolved": a.resolved, "createdAt": a.created_at.isoformat()} for a in SecurityAlert.objects.select_related("user")[:500]]
    return JsonResponse({"items": rows})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def resolve_alert(request, alert_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    alert = SecurityAlert.objects.filter(pk=alert_id).first()
    if not alert:
        return error_response("NOT_FOUND", "Security alert not found.", request.correlation_id, 404)
    alert.resolved = True
    alert.resolved_by = request.user
    alert.resolved_at = timezone.now()
    alert.save(update_fields=["resolved", "resolved_by", "resolved_at"])
    audit(request, "SECURITY_ALERT_RESOLVED", "SecurityAlert", alert.id)
    return JsonResponse({"ok": True})
