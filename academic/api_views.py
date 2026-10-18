from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.audit import audit
from core.models import SystemConfig
from core.permissions import api_view, parse_json, roles
from accounts.models import User

from .models import Course, CourseOffering, CoursePrerequisite, FacultyProfile, FeeStructure, GradeBand, GradingScheme, Program, Scholarship, Semester


def _program(p):
    return {"id": p.id, "code": p.code, "name": p.name, "durationSemesters": p.duration_semesters, "active": p.active}


@api_view()
def programs(request):
    if request.method == "GET":
        return JsonResponse({"items": [_program(p) for p in Program.objects.all()]})
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not getattr(request.user, "is_authenticated", False) or request.user.role not in {User.Role.ADMIN, User.Role.SYSADMIN}:
        return JsonResponse({"code": "FORBIDDEN", "message": "Admin access required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=403)
    data = parse_json(request)
    if not isinstance(data, dict) or not data.get("code") or not data.get("name"):
        return JsonResponse({"code": "INVALID_INPUT", "message": "code and name are required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    try:
        p = Program.objects.create(code=str(data["code"]).upper(), name=str(data["name"]), duration_semesters=int(data.get("durationSemesters", 8)))
    except Exception:
        return JsonResponse({"code": "DUPLICATE", "message": "Program code already exists", "correlationId": request.correlation_id, "fieldErrors": {}}, status=409)
    audit(request, "PROGRAM_CREATED", "Program", p.id)
    return JsonResponse(_program(p), status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def program_detail(request, program_id):
    p = Program.objects.filter(pk=program_id).first()
    if not p:
        return JsonResponse({"code": "NOT_FOUND", "message": "Program not found", "correlationId": request.correlation_id, "fieldErrors": {}}, status=404)
    if request.method == "PATCH":
        data = parse_json(request) or {}
        p.name = str(data.get("name", p.name))
        p.active = bool(data.get("active", p.active))
        p.save(update_fields=["name", "active", "updated_at"])
        audit(request, "PROGRAM_UPDATED", "Program", p.id)
        return JsonResponse(_program(p))
    if request.method == "DELETE":
        p.active = False
        p.save(update_fields=["active", "updated_at"])
        audit(request, "PROGRAM_DEACTIVATED", "Program", p.id)
        return JsonResponse({"ok": True})
    return JsonResponse(_program(p))


@api_view()
def semesters(request):
    if request.method == "GET":
        rows = [{"id": s.id, "code": s.code, "name": s.name, "startDate": s.start_date.isoformat(), "endDate": s.end_date.isoformat(), "addDropDeadline": s.add_drop_deadline.isoformat(), "isCurrent": s.is_current, "active": s.is_active} for s in Semester.objects.all()]
        return JsonResponse({"items": rows})
    if request.method != "POST" or not getattr(request.user, "is_authenticated", False) or request.user.role not in {User.Role.ADMIN, User.Role.SYSADMIN}:
        return JsonResponse({"code": "FORBIDDEN", "message": "Admin access required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=403)
    data = parse_json(request) or {}
    try:
        s = Semester.objects.create(code=data["code"], name=data["name"], start_date=parse_date(data["startDate"]), end_date=parse_date(data["endDate"]), add_drop_deadline=timezone.datetime.fromisoformat(data["addDropDeadline"].replace("Z", "+00:00")), is_current=bool(data.get("isCurrent", False)))
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid semester data", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    if s.is_current:
        Semester.objects.exclude(pk=s.pk).update(is_current=False)
    audit(request, "SEMESTER_CREATED", "Semester", s.id)
    return JsonResponse({"id": s.id, "code": s.code}, status=201)


@api_view()
def courses(request):
    if request.method == "GET":
        return JsonResponse({"items": [{"id": c.id, "code": c.code, "title": c.title, "credits": c.credits, "programIds": list(c.programs.values_list("id", flat=True))} for c in Course.objects.prefetch_related("programs")]})
    if request.method != "POST" or not getattr(request.user, "is_authenticated", False) or request.user.role not in {User.Role.ADMIN, User.Role.SYSADMIN}:
        return JsonResponse({"code": "FORBIDDEN", "message": "Admin access required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=403)
    data = parse_json(request) or {}
    try:
        c = Course.objects.create(code=str(data["code"]).upper(), title=data["title"], credits=int(data["credits"]))
        c.programs.set(data.get("programIds", []))
    except (KeyError, ValueError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid course data", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    audit(request, "COURSE_CREATED", "Course", c.id)
    return JsonResponse({"id": c.id, "code": c.code}, status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def prerequisites(request):
    if request.method == "GET":
        rows = [{"id": p.id, "courseId": p.course_id, "prerequisiteId": p.prerequisite_id, "course": p.course.code, "prerequisite": p.prerequisite.code} for p in CoursePrerequisite.objects.select_related("course", "prerequisite")]
        return JsonResponse({"items": rows})
    data = parse_json(request) or {}
    try:
        row = CoursePrerequisite.objects.create(course_id=int(data["courseId"]), prerequisite_id=int(data["prerequisiteId"]))
    except (KeyError, ValueError, Exception) as exc:
        if isinstance(exc, (KeyError, ValueError)):
            return JsonResponse({"code": "INVALID_INPUT", "message": "courseId and prerequisiteId are required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
        return JsonResponse({"code": "DUPLICATE", "message": "Prerequisite already exists", "correlationId": request.correlation_id, "fieldErrors": {}}, status=409)
    audit(request, "PREREQUISITE_CREATED", "CoursePrerequisite", row.id)
    return JsonResponse({"id": row.id}, status=201)


def _offering(o):
    return {"id": o.id, "courseId": o.course_id, "courseCode": o.course.code, "title": o.course.title, "credits": o.course.credits, "semesterId": o.semester_id, "semester": o.semester.name, "faculty": o.faculty.display_name if o.faculty else None, "capacity": o.capacity, "seatsAvailable": o.seats_available, "status": o.status, "room": o.room, "schedule": o.schedule}


@api_view()
def offerings(request):
    if request.method == "GET":
        semester_id = request.GET.get("semester")
        qs = CourseOffering.objects.select_related("course", "semester", "faculty").all()
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        return JsonResponse({"items": [_offering(o) for o in qs]})
    if request.method != "POST" or not getattr(request.user, "is_authenticated", False) or request.user.role not in {User.Role.ADMIN, User.Role.SYSADMIN}:
        return JsonResponse({"code": "FORBIDDEN", "message": "Admin access required", "correlationId": request.correlation_id, "fieldErrors": {}}, status=403)
    data = parse_json(request) or {}
    try:
        capacity = int(data["capacity"])
        o = CourseOffering.objects.create(course_id=int(data["courseId"]), semester_id=int(data["semesterId"]), faculty_id=data.get("facultyId"), capacity=capacity, seats_available=capacity, status=data.get("status", "OPEN"), room=data.get("room", ""), schedule=data.get("schedule", ""))
    except (KeyError, ValueError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid offering data", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    audit(request, "OFFERING_CREATED", "CourseOffering", o.id)
    return JsonResponse(_offering(o), status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def offering_detail(request, offering_id):
    o = CourseOffering.objects.select_related("course", "semester", "faculty").filter(pk=offering_id).first()
    if not o:
        return JsonResponse({"code": "NOT_FOUND", "message": "Offering not found", "correlationId": request.correlation_id, "fieldErrors": {}}, status=404)
    if request.method == "PATCH":
        data = parse_json(request) or {}
        if "capacity" in data:
            new_capacity = int(data["capacity"])
            enrolled = o.capacity - o.seats_available
            if new_capacity < enrolled:
                return JsonResponse({"code": "CAPACITY_TOO_LOW", "message": "Capacity cannot be below active enrollment", "correlationId": request.correlation_id, "fieldErrors": {}}, status=409)
            o.seats_available = new_capacity - enrolled
            o.capacity = new_capacity
        for key in ["status", "room", "schedule"]:
            if key in data:
                setattr(o, key, data[key])
        o.save()
        audit(request, "OFFERING_UPDATED", "CourseOffering", o.id)
    return JsonResponse(_offering(o))


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def grading_schemes(request):
    if request.method == "GET":
        rows = [{"id": s.id, "name": s.name, "version": s.version, "default": s.is_default, "bands": [{"min": str(b.minimum_score), "max": str(b.maximum_score), "letter": b.letter, "gradePoint": str(b.grade_point)} for b in s.bands.all()]} for s in GradingScheme.objects.prefetch_related("bands")]
        return JsonResponse({"items": rows})
    data = parse_json(request) or {}
    try:
        scheme = GradingScheme.objects.create(name=data["name"], version=int(data.get("version", 1)), is_default=bool(data.get("default", False)))
        if scheme.is_default:
            GradingScheme.objects.exclude(pk=scheme.pk).update(is_default=False)
        for band in data.get("bands", []):
            GradeBand.objects.create(scheme=scheme, minimum_score=band["min"], maximum_score=band["max"], letter=band["letter"], grade_point=band["gradePoint"])
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid grading scheme", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    audit(request, "GRADING_SCHEME_CREATED", "GradingScheme", scheme.id)
    return JsonResponse({"id": scheme.id}, status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def fee_structures(request):
    if request.method == "GET":
        rows = [{"id": f.id, "programId": f.program_id, "semesterId": f.semester_id, "baseFee": str(f.base_fee), "perCreditFee": str(f.per_credit_fee), "currency": f.currency, "version": f.version, "active": f.active} for f in FeeStructure.objects.all()]
        return JsonResponse({"items": rows})
    data = parse_json(request) or {}
    try:
        row = FeeStructure.objects.create(program_id=data["programId"], semester_id=data.get("semesterId"), base_fee=Decimal(str(data["baseFee"])), per_credit_fee=Decimal(str(data["perCreditFee"])), currency=data.get("currency", "INR"), version=int(data.get("version", 1)))
    except (KeyError, InvalidOperation, ValueError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid fee structure", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    audit(request, "FEE_STRUCTURE_CREATED", "FeeStructure", row.id)
    return JsonResponse({"id": row.id}, status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def scholarships(request):
    if request.method == "GET":
        rows = [{"id": s.id, "code": s.code, "name": s.name, "programId": s.program_id, "semesterId": s.semester_id, "percentage": str(s.percentage) if s.percentage is not None else None, "amount": str(s.amount) if s.amount is not None else None, "active": s.active} for s in Scholarship.objects.all()]
        return JsonResponse({"items": rows})
    data = parse_json(request) or {}
    try:
        row = Scholarship.objects.create(code=data["code"], name=data["name"], program_id=data.get("programId"), semester_id=data.get("semesterId"), percentage=data.get("percentage"), amount=data.get("amount"))
    except (KeyError, ValueError):
        return JsonResponse({"code": "INVALID_INPUT", "message": "Invalid scholarship", "correlationId": request.correlation_id, "fieldErrors": {}}, status=400)
    audit(request, "SCHOLARSHIP_CREATED", "Scholarship", row.id)
    return JsonResponse({"id": row.id}, status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def configuration(request):
    if request.method == "GET":
        rows = {row.key: row.value for row in SystemConfig.objects.all()}
        return JsonResponse(rows)
    data = parse_json(request) or {}
    for key, value in data.items():
        if key in {"attendance_threshold", "retention_years", "institution_name"}:
            SystemConfig.objects.update_or_create(key=key, defaults={"value": {"value": value}})
    audit(request, "SYSTEM_CONFIGURATION_UPDATED", "SystemConfig", "global", {"keys": list(data)})
    return JsonResponse({"ok": True})
