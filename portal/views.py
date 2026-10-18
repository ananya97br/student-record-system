from django.shortcuts import redirect, render

from accounts.models import User
from core.audit import audit


ROLE_SECTIONS = {
    User.Role.STUDENT: frozenset({"dashboard", "profile", "documents", "enrollment", "attendance", "grades", "transcript", "fees"}),
    User.Role.FACULTY: frozenset({"dashboard", "faculty"}),
    User.Role.ADMIN: frozenset({"dashboard", "admin", "reports", "audit", "configuration"}),
    User.Role.SYSADMIN: frozenset({"dashboard", "admin", "reports", "audit", "configuration"}),
}

VALID_SECTIONS = frozenset().union(*ROLE_SECTIONS.values())


def home(request):
    if getattr(request.user, "is_authenticated", False):
        return redirect("portal-page", section="dashboard")
    return redirect("login-page")


def login_page(request):
    return render(request, "login.html")


def portal_page(request, section):
    if not getattr(request.user, "is_authenticated", False):
        return redirect("login-page")
    if section not in VALID_SECTIONS:
        section = "dashboard"
    allowed_sections = ROLE_SECTIONS.get(request.user.role, frozenset({"dashboard"}))
    if section not in allowed_sections:
        audit(request, "AUTHORIZATION_DENIED", "Portal section", section, {"role": request.user.role})
        return redirect("portal-page", section="dashboard")
    return render(request, "portal.html", {"section": section, "role": request.user.role})
