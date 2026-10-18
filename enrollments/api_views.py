from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.errors import error_response
from core.permissions import api_view, login_required, parse_json
from students.models import Student

from .models import Enrollment
from .services import check_eligibility, drop_student, eligible_offerings, enroll_student


def _student(request):
    return Student.objects.select_related("program", "user").filter(user=request.user).first()


def _enrollment(row):
    offering = row.offering
    return {"id": row.id, "status": row.status, "enrolledAt": row.enrolled_at.isoformat(), "offering": {"id": offering.id, "courseCode": offering.course.code, "title": offering.course.title, "credits": offering.course.credits, "semester": offering.semester.name, "faculty": offering.faculty.display_name if offering.faculty else None}}


@api_view(require_csrf=False)
@login_required
def eligible(request):
    if request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Only students have an eligible course list.", request.correlation_id, 403)
    student = _student(request)
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    semester = request.GET.get("semester")
    rows = []
    for offering, state in eligible_offerings(student, semester=__import__("academic.models", fromlist=["Semester"]).Semester.objects.filter(pk=semester).first() if semester else None):
        rows.append({"id": offering.id, "courseCode": offering.course.code, "title": offering.course.title, "credits": offering.course.credits, "faculty": offering.faculty.display_name if offering.faculty else None, "capacity": offering.capacity, "seatsAvailable": offering.seats_available, "eligible": state.eligible, "reason": state.reason, "semester": offering.semester.name})
    return JsonResponse({"items": rows})


@csrf_exempt
@api_view()
@login_required
def my_enrollments_or_enroll(request):
    if request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Only students can manage their enrollments.", request.correlation_id, 403)
    student = _student(request)
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    if request.method == "GET":
        rows = Enrollment.objects.select_related("offering__course", "offering__semester", "offering__faculty").filter(student=student).order_by("-enrolled_at")
        return JsonResponse({"items": [_enrollment(row) for row in rows]})
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "GET or POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    try:
        row = enroll_student(request, student, int(data["offeringId"]))
    except KeyError:
        return error_response("INVALID_INPUT", "offeringId is required.", request.correlation_id, 400)
    except ValueError as exc:
        return error_response("ENROLLMENT_NOT_ALLOWED", str(exc), request.correlation_id, 409)
    except Exception:
        return error_response("NOT_FOUND", "Offering not found.", request.correlation_id, 404)
    return JsonResponse(_enrollment(row), status=201)


@csrf_exempt
@api_view()
@login_required
def drop_enrollment(request, enrollment_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    if request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Only students can drop enrollments.", request.correlation_id, 403)
    student = _student(request)
    try:
        row = drop_student(request, student, enrollment_id)
    except LookupError:
        return error_response("NOT_FOUND", "Enrollment not found.", request.correlation_id, 404)
    except ValueError as exc:
        return error_response("DROP_NOT_ALLOWED", str(exc), request.correlation_id, 409)
    return JsonResponse(_enrollment(row))
