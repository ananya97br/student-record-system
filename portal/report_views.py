from __future__ import annotations

from django.db.models import Count, Q
from django.core.cache import cache
from django.http import JsonResponse

from accounts.models import AuditLog, SecurityAlert, User
from attendance.services import percentage_for
from academic.models import CourseOffering
from core.audit import audit
from core.errors import error_response
from core.permissions import api_view, login_required, roles
from core.reports import pdf_response, xlsx_response
from enrollments.models import Enrollment
from finance.models import Invoice, Payment
from grading.models import CourseResult
from students.models import Student


def _filters(request, qs):
    if request.GET.get("semester"):
        qs = qs.filter(offering__semester_id=request.GET["semester"])
    if request.GET.get("program"):
        qs = qs.filter(student__program_id=request.GET["program"])
    if request.GET.get("course"):
        qs = qs.filter(offering__course_id=request.GET["course"])
    return qs


def _report_rows(kind, request):
    if kind == "enrollment":
        qs = Enrollment.objects.select_related("student__program", "offering__course", "offering__semester").all()
        if request.GET.get("semester"):
            qs = qs.filter(offering__semester_id=request.GET["semester"])
        if request.GET.get("program"):
            qs = qs.filter(student__program_id=request.GET["program"])
        if request.GET.get("course"):
            qs = qs.filter(offering__course_id=request.GET["course"])
        headers = ["Student ID", "Student", "Program", "Course", "Semester", "Status"]
        rows = [[r.student.student_id, r.student.full_name, r.student.program.code, r.offering.course.code, r.offering.semester.name, r.status] for r in qs.order_by("student__student_id")]
    elif kind == "attendance":
        offerings = CourseOffering.objects.select_related("course", "semester")
        if request.GET.get("semester"):
            offerings = offerings.filter(semester_id=request.GET["semester"])
        rows = []
        for offering in offerings:
            for enrollment in Enrollment.objects.select_related("student").filter(offering=offering, status=Enrollment.Status.ENROLLED):
                if request.GET.get("program") and str(enrollment.student.program_id) != request.GET["program"]:
                    continue
                summary = percentage_for(enrollment.student, offering)
                rows.append([enrollment.student.student_id, enrollment.student.full_name, offering.course.code, summary["attended"], summary["total"], summary["percentage"], "YES" if summary["belowThreshold"] else "NO"])
        headers = ["Student ID", "Student", "Course", "Attended", "Total", "Percentage", "Below threshold"]
    elif kind == "fees":
        qs = Invoice.objects.select_related("student__program", "semester")
        if request.GET.get("semester"):
            qs = qs.filter(semester_id=request.GET["semester"])
        if request.GET.get("program"):
            qs = qs.filter(student__program_id=request.GET["program"])
        headers = ["Invoice", "Student ID", "Program", "Semester", "Total", "Balance", "Status"]
        rows = [[r.invoice_number, r.student.student_id, r.student.program.code, r.semester.name, r.total, r.balance, r.status] for r in qs.order_by("student__student_id")]
    elif kind == "grades":
        qs = CourseResult.objects.select_related("student__program", "offering__course", "offering__semester").filter(is_locked=True)
        qs = _filters(request, qs)
        headers = ["Student ID", "Student", "Program", "Course", "Semester", "Score", "Grade", "Grade point"]
        rows = [[r.student.student_id, r.student.full_name, r.student.program.code, r.offering.course.code, r.offering.semester.name, r.final_score, r.letter_grade, r.grade_point] for r in qs.order_by("student__student_id")]
    else:
        return None, None
    return headers, rows


@api_view(require_csrf=False)
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def report(request, kind):
    if kind not in {"enrollment", "attendance", "fees", "grades"}:
        return error_response("NOT_FOUND", "Unknown report.", request.correlation_id, 404)
    headers, rows = _report_rows(kind, request)
    if request.GET.get("format"):
        key = f"srs-rate:export:{request.user.pk}"
        count = cache.get(key, 0)
        if count >= 10:
            return error_response("RATE_LIMITED", "Too many exports. Try again later.", request.correlation_id, 429)
        cache.set(key, count + 1, 60)
    audit(request, "REPORT_EXPORT" if request.GET.get("format") else "REPORT_VIEW", "Report", kind, {"filters": {key: request.GET.get(key) for key in ["semester", "program", "course"] if request.GET.get(key)}})
    export_format = request.GET.get("format")
    if export_format == "xlsx":
        return xlsx_response(f"{kind}-report.xlsx", headers, rows[:10000])
    if export_format == "pdf":
        return pdf_response(f"{kind}-report.pdf", f"{kind.title()} report", headers, rows[:2000])
    try:
        page = max(1, int(request.GET.get("page", 1)))
        size = min(100, max(1, int(request.GET.get("pageSize", 25))))
    except ValueError:
        page, size = 1, 25
    start = (page - 1) * size
    data = [dict(zip(headers, row)) for row in rows[start : start + size]]
    return JsonResponse({"kind": kind, "headers": headers, "items": data, "page": page, "pageSize": size, "total": len(rows)})


@api_view(require_csrf=False)
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def audit_list(request):
    rows = [{"id": row.id, "createdAt": row.created_at.isoformat(), "actor": row.actor.login_id if row.actor else "system", "action": row.action, "entityType": row.entity_type, "entityId": row.entity_id, "correlationId": row.correlation_id, "metadata": row.metadata} for row in AuditLog.objects.select_related("actor")[:1000]]
    return JsonResponse({"items": rows})


@api_view(require_csrf=False)
@login_required
def dashboard(request):
    if request.user.role == User.Role.STUDENT:
        student = Student.objects.filter(user=request.user).first()
        from attendance.services import percentage_for

        enrollments = Enrollment.objects.select_related("offering__course").filter(student=student, status=Enrollment.Status.ENROLLED)
        attendance_warnings = sum(1 for row in enrollments if percentage_for(student, row.offering)["belowThreshold"])
        invoice_balance = sum((invoice.balance for invoice in Invoice.objects.filter(student=student)), 0)
        return JsonResponse({"role": "STUDENT", "courses": enrollments.count(), "attendanceWarnings": attendance_warnings, "outstandingBalance": str(invoice_balance)})
    if request.user.role == User.Role.FACULTY:
        offerings = CourseOffering.objects.filter(faculty__user=request.user)
        return JsonResponse({"role": "FACULTY", "assignedOfferings": offerings.count(), "pendingAttendance": offerings.count()})
    return JsonResponse({"role": request.user.role, "students": Student.objects.count(), "pendingProfileChanges": __import__("students.models", fromlist=["ProfileChangeRequest"]).ProfileChangeRequest.objects.filter(status="PENDING").count(), "openAlerts": SecurityAlert.objects.filter(resolved=False).count(), "unpaidInvoices": Invoice.objects.filter(status__in=["UNPAID", "PENDING", "PARTIAL"]).count()})
