from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from academic.models import CourseOffering, Semester
from core.audit import audit
from core.notifications import notify

from .models import Enrollment


@dataclass
class Eligibility:
    eligible: bool
    reason: str = ""


def prerequisite_state(student, course) -> tuple[bool, list[str]]:
    from grading.models import CourseResult

    completed_codes = set(CourseResult.objects.filter(student=student, is_locked=True, grade_point__gt=0).values_list("offering__course__code", flat=True))
    missing = list(course.prerequisite_links.exclude(prerequisite__code__in=completed_codes).values_list("prerequisite__code", flat=True))
    return not missing, missing


def check_eligibility(student, offering, now=None) -> Eligibility:
    now = now or timezone.now()
    if offering.status != CourseOffering.Status.OPEN:
        return Eligibility(False, "Offering is not open.")
    if not offering.semester.is_active or (offering.semester.start_date > now.date() or offering.semester.end_date < now.date()):
        # Demo data can have an active current semester; date is authoritative.
        return Eligibility(False, "Offering is outside its active semester.")
    if not offering.course.programs.filter(pk=student.program_id).exists():
        return Eligibility(False, "Course is not part of your program.")
    passed, missing = prerequisite_state(student, offering.course)
    if not passed:
        return Eligibility(False, f"Prerequisite(s) incomplete: {', '.join(missing)}")
    existing = Enrollment.objects.filter(student=student, offering=offering).first()
    if existing and existing.status in {Enrollment.Status.ENROLLED, Enrollment.Status.COMPLETED}:
        return Eligibility(False, "You are already enrolled in this offering.")
    if offering.seats_available < 1:
        return Eligibility(False, "No seats are available.")
    if now > offering.semester.add_drop_deadline:
        return Eligibility(False, "The add/drop window has closed.")
    return Eligibility(True)


def eligible_offerings(student, semester=None):
    semester = semester or Semester.objects.filter(is_current=True, is_active=True).first()
    if not semester:
        return []
    offerings = CourseOffering.objects.select_related("course", "semester", "faculty").prefetch_related("course__programs", "course__prerequisite_links__prerequisite").filter(semester=semester)
    return [(offering, check_eligibility(student, offering)) for offering in offerings]


def enroll_student(request, student, offering_id):
    with transaction.atomic():
        offering = CourseOffering.objects.select_for_update().select_related("course", "semester", "faculty").get(pk=offering_id)
        state = check_eligibility(student, offering)
        if not state.eligible:
            raise ValueError(state.reason)
        enrollment, _ = Enrollment.objects.update_or_create(student=student, offering=offering, defaults={"status": Enrollment.Status.ENROLLED, "dropped_at": None})
        offering.seats_available -= 1
        offering.save(update_fields=["seats_available", "updated_at"])
        audit(request, "ENROLLMENT_CREATED", "Enrollment", enrollment.id, {"offeringId": offering.id})
        transaction.on_commit(lambda: notify(student.user, "Enrollment confirmed", f"Your enrollment in {offering.course.code} — {offering.course.title} is confirmed.", safe_metadata={"enrollmentId": enrollment.id}))
    return enrollment


def drop_student(request, student, enrollment_id):
    with transaction.atomic():
        enrollment = Enrollment.objects.select_for_update().select_related("offering__semester", "offering__course").filter(pk=enrollment_id, student=student).first()
        if not enrollment:
            raise LookupError("Enrollment not found")
        if enrollment.status != Enrollment.Status.ENROLLED:
            raise ValueError("Only an active enrollment can be dropped")
        if timezone.now() > enrollment.offering.semester.add_drop_deadline:
            raise ValueError("The add/drop window has closed")
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.dropped_at = timezone.now()
        enrollment.save(update_fields=["status", "dropped_at", "updated_at"])
        offering = CourseOffering.objects.select_for_update().get(pk=enrollment.offering_id)
        offering.seats_available = min(offering.capacity, offering.seats_available + 1)
        offering.save(update_fields=["seats_available", "updated_at"])
        audit(request, "ENROLLMENT_DROPPED", "Enrollment", enrollment.id, {"offeringId": offering.id})
    return enrollment
