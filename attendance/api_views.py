from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from academic.models import CourseOffering
from core.audit import audit
from core.errors import error_response
from core.permissions import api_view, login_required, parse_json, roles
from core.reports import xlsx_response
from enrollments.models import Enrollment
from students.models import Student

from .models import AttendanceRecord, AttendanceSession
from .services import can_edit, percentage_for, threshold


def _faculty_can(request, offering):
    if request.user.role in {User.Role.ADMIN, User.Role.SYSADMIN}:
        return True
    return request.user.role == User.Role.FACULTY and offering.faculty and offering.faculty.user_id == request.user.pk


def _offering(row):
    return {"id": row.id, "courseCode": row.course.code, "title": row.course.title, "semester": row.semester.name, "capacity": row.capacity, "seatsAvailable": row.seats_available, "status": row.status}


@api_view(require_csrf=False)
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def faculty_offerings(request):
    qs = CourseOffering.objects.select_related("course", "semester", "faculty")
    if request.user.role == User.Role.FACULTY:
        qs = qs.filter(faculty__user=request.user)
    return JsonResponse({"items": [_offering(row) for row in qs]})


@api_view(require_csrf=False)
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def roster(request, offering_id):
    offering = CourseOffering.objects.select_related("course", "semester", "faculty").filter(pk=offering_id).first()
    if not offering:
        return error_response("NOT_FOUND", "Offering not found.", request.correlation_id, 404)
    if not _faculty_can(request, offering):
        audit(request, "AUTHORIZATION_DENIED", "CourseOffering", offering.id)
        return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
    rows = [{"studentId": e.student_id, "systemId": e.student.student_id, "name": e.student.full_name, "email": e.student.user.email} for e in Enrollment.objects.select_related("student__user").filter(offering=offering, status=Enrollment.Status.ENROLLED)]
    return JsonResponse({"items": rows})


@csrf_exempt
@api_view()
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def sessions(request, offering_id):
    offering = CourseOffering.objects.select_related("course", "semester", "faculty").filter(pk=offering_id).first()
    if not offering:
        return error_response("NOT_FOUND", "Offering not found.", request.correlation_id, 404)
    if not _faculty_can(request, offering):
        audit(request, "AUTHORIZATION_DENIED", "CourseOffering", offering.id)
        return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
    if request.method == "GET":
        rows = [{"id": s.id, "sessionAt": s.session_at.isoformat(), "topic": s.topic, "editable": can_edit(s)} for s in offering.attendance_sessions.all()]
        return JsonResponse({"items": rows})
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "GET or POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    session_at = parse_datetime(str(data.get("sessionAt", "")))
    if not session_at:
        return error_response("INVALID_INPUT", "sessionAt must be an ISO timestamp.", request.correlation_id, 400)
    if timezone.is_naive(session_at):
        session_at = timezone.make_aware(session_at)
    try:
        row = AttendanceSession.objects.create(offering=offering, session_at=session_at, topic=str(data.get("topic", ""))[:200], created_by=request.user)
    except Exception:
        return error_response("DUPLICATE", "A session already exists at this time.", request.correlation_id, 409)
    audit(request, "ATTENDANCE_SESSION_CREATED", "AttendanceSession", row.id, {"offeringId": offering.id})
    return JsonResponse({"id": row.id, "sessionAt": row.session_at.isoformat()}, status=201)


@csrf_exempt
@api_view()
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def bulk_records(request, session_id):
    session = AttendanceSession.objects.select_related("offering__faculty", "offering__course").filter(pk=session_id).first()
    if not session:
        return error_response("NOT_FOUND", "Attendance session not found.", request.correlation_id, 404)
    if not _faculty_can(request, session.offering):
        audit(request, "AUTHORIZATION_DENIED", "AttendanceSession", session.id)
        return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
    if not can_edit(session):
        return error_response("ATTENDANCE_WINDOW_CLOSED", "Attendance can only be edited within 48 hours.", request.correlation_id, 409)
    data = parse_json(request) or {}
    records = data.get("records")
    if not isinstance(records, list):
        return error_response("INVALID_INPUT", "records must be a list.", request.correlation_id, 400)
    valid_statuses = {choice for choice, _ in AttendanceRecord.Status.choices}
    enrolled = set(Enrollment.objects.filter(offering=session.offering, status=Enrollment.Status.ENROLLED).values_list("student_id", flat=True))
    with transaction.atomic():
        for item in records:
            try:
                student_id = int(item["studentId"])
                status = str(item["status"])
            except (KeyError, ValueError, TypeError):
                return error_response("INVALID_INPUT", "Each record needs studentId and status.", request.correlation_id, 400)
            if student_id not in enrolled or status not in valid_statuses:
                return error_response("INVALID_ATTENDANCE", "Student is not enrolled or status is invalid.", request.correlation_id, 400)
            previous = AttendanceRecord.objects.filter(session=session, student_id=student_id).first()
            AttendanceRecord.objects.update_or_create(session=session, student_id=student_id, defaults={"status": status, "marked_by": request.user})
            if previous and previous.status != status:
                audit(request, "ATTENDANCE_CORRECTED", "AttendanceRecord", previous.id, {"from": previous.status, "to": status})
    audit(request, "ATTENDANCE_BULK_SAVED", "AttendanceSession", session.id, {"count": len(records)})
    return JsonResponse({"saved": len(records), "threshold": threshold()})


@api_view(require_csrf=False)
@login_required
def student_summary(request):
    if request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Student access required.", request.correlation_id, 403)
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    rows = []
    for enrollment in Enrollment.objects.select_related("offering__course", "offering__semester").filter(student=student, status=Enrollment.Status.ENROLLED):
        rows.append({"offeringId": enrollment.offering_id, "courseCode": enrollment.offering.course.code, "title": enrollment.offering.course.title, **percentage_for(student, enrollment.offering)})
    return JsonResponse({"items": rows, "threshold": threshold()})


@api_view(require_csrf=False)
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def flagged(request):
    offering_id = request.GET.get("offering")
    offerings = CourseOffering.objects.select_related("course", "faculty")
    if request.user.role == User.Role.FACULTY:
        offerings = offerings.filter(faculty__user=request.user)
    if offering_id:
        offerings = offerings.filter(pk=offering_id)
    rows = []
    for offering in offerings:
        for enrollment in Enrollment.objects.select_related("student").filter(offering=offering, status=Enrollment.Status.ENROLLED):
            summary = percentage_for(enrollment.student, offering)
            if summary["belowThreshold"]:
                rows.append([enrollment.student.student_id, enrollment.student.full_name, offering.course.code, summary["attended"], summary["total"], summary["percentage"]])
    if request.GET.get("format") == "xlsx":
        audit(request, "REPORT_EXPORT", "Attendance", offering_id or "all")
        return xlsx_response("attendance-flagged.xlsx", ["Student ID", "Student", "Course", "Attended", "Total", "Percentage"], rows)
    return JsonResponse({"items": [{"studentId": r[0], "student": r[1], "course": r[2], "attended": r[3], "total": r[4], "percentage": r[5]} for r in rows], "threshold": threshold()})
