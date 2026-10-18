from __future__ import annotations

import hashlib
import hmac
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import User
from academic.models import CourseOffering
from core.audit import audit
from core.errors import error_response
from core.permissions import api_view, login_required, parse_json, roles
from enrollments.models import Enrollment
from students.models import Student

from .models import AssessmentComponent, CourseResult, GradeRecord, TranscriptVerification
from .services import calculate_score, finalize, gpa_for, transcript_code


def _can_teach(request, offering):
    return request.user.role in {User.Role.ADMIN, User.Role.SYSADMIN} or (request.user.role == User.Role.FACULTY and offering.faculty and offering.faculty.user_id == request.user.pk)


@csrf_exempt
@api_view()
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def components(request):
    if request.method == "GET":
        offering_id = request.GET.get("offering")
        qs = AssessmentComponent.objects.select_related("offering__course")
        if offering_id:
            qs = qs.filter(offering_id=offering_id)
        return JsonResponse({"items": [{"id": c.id, "offeringId": c.offering_id, "name": c.name, "type": c.component_type, "maxMarks": str(c.max_marks), "weight": str(c.weight)} for c in qs]})
    data = parse_json(request) or {}
    try:
        offering = CourseOffering.objects.select_related("faculty").get(pk=data["offeringId"])
        if not _can_teach(request, offering):
            return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
        component = AssessmentComponent.objects.create(offering=offering, name=data["name"], component_type=data.get("type", "OTHER"), max_marks=Decimal(str(data["maxMarks"])), weight=Decimal(str(data["weight"])))
    except (KeyError, InvalidOperation, ValueError):
        return error_response("INVALID_INPUT", "Invalid assessment component.", request.correlation_id, 400)
    audit(request, "ASSESSMENT_COMPONENT_CREATED", "AssessmentComponent", component.id)
    return JsonResponse({"id": component.id}, status=201)


@csrf_exempt
@api_view()
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def bulk_marks(request, component_id):
    component = AssessmentComponent.objects.select_related("offering__faculty", "offering__course").filter(pk=component_id).first()
    if not component:
        return error_response("NOT_FOUND", "Assessment component not found.", request.correlation_id, 404)
    if not _can_teach(request, component.offering):
        audit(request, "AUTHORIZATION_DENIED", "AssessmentComponent", component.id)
        return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
    data = parse_json(request) or {}
    marks = data.get("marks")
    if not isinstance(marks, list):
        return error_response("INVALID_INPUT", "marks must be a list.", request.correlation_id, 400)
    for item in marks:
        try:
            result = CourseResult.objects.filter(student_id=item["studentId"], offering=component.offering, is_locked=True).first()
            if result:
                return error_response("GRADE_LOCKED", "Finalized grades cannot be edited by faculty.", request.correlation_id, 409)
            mark = Decimal(str(item["mark"]))
            if mark < 0 or mark > component.max_marks:
                return error_response("MARK_OUT_OF_RANGE", "Mark must be between zero and max marks.", request.correlation_id, 400)
            if not Enrollment.objects.filter(student_id=item["studentId"], offering=component.offering, status=Enrollment.Status.ENROLLED).exists():
                return error_response("INVALID_STUDENT", "Student is not enrolled in the offering.", request.correlation_id, 400)
            GradeRecord.objects.update_or_create(component=component, student_id=item["studentId"], defaults={"mark": mark, "entered_by": request.user})
        except (KeyError, InvalidOperation, ValueError, TypeError):
            return error_response("INVALID_INPUT", "Each mark needs studentId and a numeric mark.", request.correlation_id, 400)
    audit(request, "GRADE_BULK_SAVED", "AssessmentComponent", component.id, {"count": len(marks)})
    return JsonResponse({"saved": len(marks)})


@csrf_exempt
@api_view()
@roles(User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN)
def finalize_offering(request, offering_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    offering = CourseOffering.objects.select_related("faculty", "course").filter(pk=offering_id).first()
    if not offering:
        return error_response("NOT_FOUND", "Offering not found.", request.correlation_id, 404)
    if not _can_teach(request, offering):
        audit(request, "AUTHORIZATION_DENIED", "CourseOffering", offering.id)
        return error_response("FORBIDDEN", "You are not assigned to this offering.", request.correlation_id, 403)
    try:
        rows = finalize(request, offering)
    except ValueError as exc:
        return error_response("FINALIZATION_FAILED", str(exc), request.correlation_id, 409)
    return JsonResponse({"locked": rows.count(), "offeringId": offering.id})


@api_view(require_csrf=False)
@login_required
def results(request):
    if request.user.role == User.Role.STUDENT:
        student = Student.objects.filter(user=request.user).first()
        qs = CourseResult.objects.select_related("offering__course", "offering__semester").filter(student=student, is_locked=True)
    elif request.user.role in {User.Role.FACULTY, User.Role.ADMIN, User.Role.SYSADMIN}:
        qs = CourseResult.objects.select_related("student", "offering__course", "offering__semester")
        if request.user.role == User.Role.FACULTY:
            qs = qs.filter(offering__faculty__user=request.user)
    else:
        return error_response("FORBIDDEN", "Not authorized.", request.correlation_id, 403)
    rows = [{"id": r.id, "studentId": r.student.student_id, "studentName": r.student.full_name, "offeringId": r.offering_id, "courseCode": r.offering.course.code, "courseTitle": r.offering.course.title, "semester": r.offering.semester.name, "score": str(r.final_score) if r.final_score is not None else None, "letter": r.letter_grade, "gradePoint": str(r.grade_point), "locked": r.is_locked} for r in qs[:1000]]
    return JsonResponse({"items": rows})


@csrf_exempt
@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def override_result(request, result_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    result = CourseResult.objects.select_related("student", "offering__course").filter(pk=result_id).first()
    if not result:
        return error_response("NOT_FOUND", "Course result not found.", request.correlation_id, 404)
    data = parse_json(request) or {}
    reason = str(data.get("reason", "")).strip()
    if not reason:
        return error_response("REASON_REQUIRED", "An override reason is mandatory.", request.correlation_id, 400)
    try:
        if "finalScore" in data:
            score = Decimal(str(data["finalScore"]))
            if score < 0 or score > 100:
                raise ValueError
            result.final_score = score
        if "letterGrade" in data:
            result.letter_grade = str(data["letterGrade"])[:5]
        if "gradePoint" in data:
            result.grade_point = Decimal(str(data["gradePoint"]))
    except (InvalidOperation, ValueError):
        return error_response("INVALID_INPUT", "Override grade values are invalid.", request.correlation_id, 400)
    result.is_locked = True
    result.locked_by = request.user
    result.overridden_by = request.user
    result.override_reason = reason[:500]
    result.finalized_at = timezone.now()
    result.save()
    audit(request, "GRADE_ADMIN_OVERRIDE", "CourseResult", result.id, {"reason": reason[:200]})
    return JsonResponse({"id": result.id, "locked": True, "override": True})


@api_view(require_csrf=False)
@login_required
def gpa(request):
    if request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Student access required.", request.correlation_id, 403)
    student = Student.objects.filter(user=request.user).first()
    data = gpa_for(student)
    return JsonResponse({"cgpa": str(data["cgpa"]), "semesters": [{"semester": row["semester"], "gpa": str(row["gpa"]), "courses": [{"courseCode": r.offering.course.code, "title": r.offering.course.title, "credits": r.offering.course.credits, "letter": r.letter_grade, "gradePoint": str(r.grade_point), "score": str(r.final_score)} for r in row["courses"]]} for row in data["semesters"]]})


def _student_for_request(request):
    if request.user.role == User.Role.STUDENT:
        return Student.objects.select_related("program", "user").filter(user=request.user).first()
    student_id = request.GET.get("student")
    return Student.objects.select_related("program", "user").filter(pk=student_id).first() if student_id else None


@api_view(require_csrf=False)
@login_required
def transcript(request):
    if request.user.role not in {User.Role.STUDENT, User.Role.ADMIN, User.Role.SYSADMIN}:
        return error_response("FORBIDDEN", "Only the student or an authorized administrator may generate this transcript.", request.correlation_id, 403)
    student = _student_for_request(request)
    if not student:
        return error_response("NOT_FOUND", "Student profile not found or student parameter is required.", request.correlation_id, 404)
    results_qs = list(CourseResult.objects.select_related("offering__course", "offering__semester").filter(student=student, is_locked=True).order_by("offering__semester__start_date", "offering__course__code"))
    verification, snapshot_hash = transcript_code(student, results_qs)
    gpa_data = gpa_for(student)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    flow = [Paragraph("Student Record System", styles["Title"]), Paragraph("Official Academic Transcript", styles["Heading2"]), Spacer(1, 12), Paragraph(f"Student: {student.full_name} ({student.student_id})", styles["BodyText"]), Paragraph(f"Program: {student.program.code} — {student.program.name}", styles["BodyText"]), Spacer(1, 12)]
    data = [["Semester", "Course", "Credits", "Grade", "Grade point"]]
    for result in results_qs:
        data.append([result.offering.semester.name, f"{result.offering.course.code} — {result.offering.course.title}", str(result.offering.course.credits), result.letter_grade, str(result.grade_point)])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    flow += [table, Spacer(1, 12), Paragraph(f"CGPA: {gpa_data['cgpa']}", styles["Heading3"]), Paragraph(f"Verification code: {verification.code}", styles["BodyText"]), Paragraph(f"Generated: {verification.generated_at.isoformat()}", styles["BodyText"])]
    doc.build(flow)
    audit(request, "TRANSCRIPT_GENERATED", "TranscriptVerification", verification.id, {"studentId": student.student_id})
    return HttpResponse(output.getvalue(), content_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="transcript.pdf"'})


@api_view(require_csrf=False)
def verify_transcript(request, code):
    verification = TranscriptVerification.objects.select_related("student__program").filter(code=code).first()
    if not verification:
        return error_response("NOT_FOUND", "Transcript verification code not found.", request.correlation_id, 404)
    results_qs = CourseResult.objects.select_related("offering__course", "offering__semester").filter(student=verification.student, is_locked=True).order_by("offering__semester__start_date", "offering__course__code")
    snapshot = "|".join(f"{result.id}:{result.final_score}:{result.letter_grade}:{result.grade_point}" for result in results_qs)
    valid = hmac.compare_digest(verification.snapshot_hash, hashlib.sha256(snapshot.encode()).hexdigest())
    audit(request, "TRANSCRIPT_VERIFIED", "TranscriptVerification", verification.id)
    return JsonResponse({"valid": valid, "code": verification.code, "student": verification.student.full_name, "studentId": verification.student.student_id, "program": verification.student.program.name, "generatedAt": verification.generated_at.isoformat(), "results": [{"semester": r.offering.semester.name, "course": r.offering.course.code, "letter": r.letter_grade, "gradePoint": str(r.grade_point)} for r in results_qs], "cgpa": str(gpa_for(verification.student)["cgpa"])})
