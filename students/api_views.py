from __future__ import annotations

import hashlib
import mimetypes
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.audit import audit
from core.errors import error_response
from core.permissions import api_view, login_required, parse_json, roles
from core.scanner import get_scanner

from .models import ProfileChangeRequest, Student, StudentDocument
from .services import next_student_id


def _student_data(student, include_contact=False):
    result = {"id": student.id, "studentId": student.student_id, "firstName": student.first_name, "lastName": student.last_name, "fullName": student.full_name, "email": student.user.email, "program": {"id": student.program_id, "code": student.program.code, "name": student.program.name}, "status": student.status}
    if include_contact:
        result.update({"phone": student.phone, "address": student.address, "emergencyContactName": student.emergency_contact_name, "emergencyContactPhone": student.emergency_contact_phone})
    return result


@api_view(require_csrf=False)
@login_required
def my_profile(request):
    student = Student.objects.select_related("user", "program").filter(user=request.user).first()
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    if request.method == "GET":
        return JsonResponse(_student_data(student, include_contact=True))
    if request.method != "PATCH" or request.user.role != User.Role.STUDENT:
        return error_response("FORBIDDEN", "Students may only submit profile change requests.", request.correlation_id, 403)
    data = parse_json(request) or {}
    fields = {"phone": "phone", "address": "address", "emergencyContactName": "emergency_contact_name", "emergencyContactPhone": "emergency_contact_phone"}
    created = []
    with transaction.atomic():
        for incoming, field in fields.items():
            if incoming in data:
                value = str(data[incoming]).strip()
                if not value or len(value) > 500:
                    return error_response("INVALID_INPUT", f"{incoming} is invalid.", request.correlation_id, 400)
                old_value = getattr(student, field)
                ProfileChangeRequest.objects.filter(student=student, field=field, status=ProfileChangeRequest.Status.PENDING).update(status=ProfileChangeRequest.Status.REJECTED, reviewer=request.user, review_reason="Superseded by a newer request", reviewed_at=timezone.now())
                created.append(ProfileChangeRequest.objects.create(student=student, field=field, old_value=old_value, new_value=value))
    for row in created:
        audit(request, "PROFILE_CHANGE_REQUESTED", "ProfileChangeRequest", row.id, {"field": row.field})
    return JsonResponse({"message": "Changes submitted for administrator approval.", "requestIds": [row.id for row in created]}, status=202)


@api_view(require_csrf=False)
@login_required
def my_change_requests(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    rows = [{"id": row.id, "field": row.field, "oldValue": row.old_value, "newValue": row.new_value, "status": row.status, "reason": row.review_reason, "createdAt": row.created_at.isoformat()} for row in student.profile_change_requests.all()]
    return JsonResponse({"items": rows})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def change_requests(request):
    rows = [{"id": row.id, "studentId": row.student.student_id, "studentName": row.student.full_name, "field": row.field, "oldValue": row.old_value, "newValue": row.new_value, "status": row.status, "createdAt": row.created_at.isoformat()} for row in ProfileChangeRequest.objects.select_related("student").filter(status=ProfileChangeRequest.Status.PENDING)]
    return JsonResponse({"items": rows})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def change_request_decision(request, request_id):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    decision = data.get("decision")
    row = ProfileChangeRequest.objects.select_related("student").filter(pk=request_id).first()
    if not row:
        return error_response("NOT_FOUND", "Change request not found.", request.correlation_id, 404)
    if row.status != ProfileChangeRequest.Status.PENDING:
        return error_response("ALREADY_REVIEWED", "This request has already been reviewed.", request.correlation_id, 409)
    with transaction.atomic():
        row = ProfileChangeRequest.objects.select_for_update().get(pk=row.pk)
        row.status = ProfileChangeRequest.Status.APPROVED if decision == "APPROVE" else ProfileChangeRequest.Status.REJECTED
        row.reviewer = request.user
        row.review_reason = str(data.get("reason", ""))[:500]
        row.reviewed_at = timezone.now()
        row.save(update_fields=["status", "reviewer", "review_reason", "reviewed_at"])
        if row.status == ProfileChangeRequest.Status.APPROVED:
            setattr(row.student, row.field, row.new_value)
            row.student.save(update_fields=[row.field, "updated_at"])
    audit(request, f"PROFILE_CHANGE_{row.status}", "ProfileChangeRequest", row.id, {"field": row.field})
    return JsonResponse({"id": row.id, "status": row.status})


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def student_list_or_create(request):
    if request.method == "GET":
        query = request.GET.get("q", "").strip()
        qs = Student.objects.select_related("user", "program").all()
        if query:
            from django.db.models import Q

            qs = qs.filter(Q(student_id__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(user__email__icontains=query))
        return JsonResponse({"items": [_student_data(s) for s in qs[:500]]})
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "GET or POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    required = ["email", "password", "firstName", "lastName", "programId"]
    if any(not data.get(key) for key in required):
        return error_response("INVALID_INPUT", "email, password, firstName, lastName, and programId are required.", request.correlation_id, 400)
    if len(str(data["password"])) < 10:
        return error_response("WEAK_PASSWORD", "Password must be at least 10 characters.", request.correlation_id, 400)
    with transaction.atomic():
        try:
            user = User.objects.create_user(login_id=data.get("loginId") or f"student-{uuid.uuid4().hex[:10]}", email=data["email"], password=data["password"], role=User.Role.STUDENT)
            student = Student.objects.create(user=user, student_id=next_student_id(), program_id=data["programId"], first_name=data["firstName"], last_name=data["lastName"], phone=data.get("phone", ""), address=data.get("address", ""), emergency_contact_name=data.get("emergencyContactName", ""), emergency_contact_phone=data.get("emergencyContactPhone", ""))
        except Exception as exc:
            return error_response("INVALID_RECORD", "Could not create student; check unique fields and program.", request.correlation_id, 400)
    audit(request, "STUDENT_CREATED", "Student", student.id, {"studentId": student.student_id})
    return JsonResponse(_student_data(student, include_contact=True), status=201)


@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def student_detail(request, student_pk):
    student = Student.objects.select_related("user", "program").filter(pk=student_pk).first()
    if not student:
        return error_response("NOT_FOUND", "Student not found.", request.correlation_id, 404)
    return JsonResponse(_student_data(student, include_contact=True))


def _allowed_file(filename, content_type, content):
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".jpg", ".jpeg"}:
        return False, "Only PDF and JPEG files are accepted."
    if content_type not in {"application/pdf", "image/jpeg", "image/jpg"}:
        return False, "The declared MIME type is not allowed."
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        return False, "The PDF file signature is invalid."
    if extension in {".jpg", ".jpeg"} and not (content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9")):
        return False, "The JPEG file signature is invalid."
    return True, ""


@csrf_exempt
@api_view()
@login_required
def my_documents(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return error_response("NOT_FOUND", "Student profile not found.", request.correlation_id, 404)
    if request.method == "GET":
        rows = [{"id": str(d.id), "name": d.original_name, "contentType": d.content_type, "size": d.size_bytes, "status": d.scan_status, "uploadedAt": d.uploaded_at.isoformat()} for d in student.documents.all()]
        return JsonResponse({"items": rows})
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "GET or POST is required.", request.correlation_id, 405)
    uploaded = request.FILES.get("file")
    if not uploaded:
        return error_response("INVALID_INPUT", "A file is required.", request.correlation_id, 400)
    if uploaded.size > 5 * 1024 * 1024:
        return error_response("FILE_TOO_LARGE", "Files must be 5 MB or smaller.", request.correlation_id, 400)
    content = uploaded.read()
    valid, message = _allowed_file(uploaded.name, uploaded.content_type, content)
    if not valid:
        return error_response("INVALID_FILE", message, request.correlation_id, 400)
    scan = get_scanner().scan(content)
    if scan != "CLEAN":
        audit(request, "DOCUMENT_REJECTED", "StudentDocument", "scanner", {"studentId": student.student_id, "reason": scan})
        return error_response("MALWARE_DETECTED", "The uploaded document failed the malware scan.", request.correlation_id, 400)
    extension = Path(uploaded.name).suffix.lower()
    storage_key = f"{student.student_id}/{uuid.uuid4().hex}{extension}"
    destination = Path(settings.MEDIA_ROOT) / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    document = StudentDocument.objects.create(student=student, original_name=os.path.basename(uploaded.name)[:255], storage_key=storage_key, content_type=uploaded.content_type, extension=extension, size_bytes=len(content), checksum_sha256=hashlib.sha256(content).hexdigest(), scan_status=StudentDocument.ScanStatus.CLEAN, scanned_at=timezone.now())
    audit(request, "DOCUMENT_UPLOADED", "StudentDocument", document.id, {"studentId": student.student_id, "size": len(content)})
    return JsonResponse({"id": str(document.id), "name": document.original_name, "status": document.scan_status}, status=201)


@api_view(require_csrf=False)
@login_required
def download_document(request, document_id):
    document = StudentDocument.objects.select_related("student").filter(pk=document_id, scan_status=StudentDocument.ScanStatus.CLEAN).first()
    if not document:
        return error_response("NOT_FOUND", "Document not found.", request.correlation_id, 404)
    is_owner = document.student.user_id == request.user.pk
    if not is_owner and request.user.role not in {User.Role.ADMIN, User.Role.SYSADMIN}:
        audit(request, "AUTHORIZATION_DENIED", "StudentDocument", document.id)
        return error_response("FORBIDDEN", "You are not authorized to download this document.", request.correlation_id, 403)
    path = Path(settings.MEDIA_ROOT) / document.storage_key
    if not path.is_file() or Path(os.path.realpath(path)).is_relative_to(Path(os.path.realpath(settings.MEDIA_ROOT))) is False:
        return error_response("NOT_FOUND", "Document content is unavailable.", request.correlation_id, 404)
    audit(request, "DOCUMENT_DOWNLOADED", "StudentDocument", document.id)
    response = FileResponse(path.open("rb"), content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.original_name.replace(chr(34), "")}"'
    return response
