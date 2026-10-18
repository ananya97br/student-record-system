from __future__ import annotations

import hashlib
import secrets
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from academic.models import GradeBand, GradingScheme
from core.audit import audit

from .models import AssessmentComponent, CourseResult, GradeRecord, TranscriptVerification


def default_scheme():
    return GradingScheme.objects.filter(is_default=True, active=True).prefetch_related("bands").first() or GradingScheme.objects.filter(active=True).prefetch_related("bands").first()


def band_for(score: Decimal, scheme=None):
    scheme = scheme or default_scheme()
    if not scheme:
        raise ValueError("No active grading scheme is configured")
    return scheme.bands.filter(minimum_score__lte=score, maximum_score__gte=score).order_by("-minimum_score").first()


def calculate_score(student, offering):
    components = list(AssessmentComponent.objects.filter(offering=offering))
    if not components:
        raise ValueError("No assessment components are configured")
    records = {record.component_id: record for record in GradeRecord.objects.filter(student=student, component__offering=offering)}
    if len(records) < len(components):
        raise ValueError("Every assessment component needs a mark before finalization")
    total_weight = sum((component.weight for component in components), Decimal("0"))
    if total_weight <= 0:
        raise ValueError("Assessment weights must be positive")
    score = sum((records[component.id].mark / component.max_marks * component.weight for component in components), Decimal("0"))
    score = (score / total_weight * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    band = band_for(score)
    if not band:
        raise ValueError("Score does not fit any configured grade band")
    return score, band


def finalize(request, offering):
    from enrollments.models import Enrollment

    with transaction.atomic():
        for enrollment in Enrollment.objects.select_related("student").filter(offering=offering, status=Enrollment.Status.ENROLLED):
            score, band = calculate_score(enrollment.student, offering)
            result, _ = CourseResult.objects.select_for_update().get_or_create(student=enrollment.student, offering=offering)
            result.final_score = score
            result.letter_grade = band.letter
            result.grade_point = band.grade_point
            result.is_locked = True
            result.finalized_at = timezone.now()
            result.locked_by = request.user
            result.save()
            audit(request, "GRADE_LOCKED", "CourseResult", result.id, {"offeringId": offering.id})
    return CourseResult.objects.filter(offering=offering, is_locked=True)


def gpa_for(student):
    results = CourseResult.objects.select_related("offering__course", "offering__semester").filter(student=student, is_locked=True)
    semesters = {}
    for result in results:
        bucket = semesters.setdefault(result.offering.semester_id, {"semester": result.offering.semester.name, "credits": Decimal("0"), "points": Decimal("0"), "courses": []})
        credits = Decimal(result.offering.course.credits)
        bucket["credits"] += credits
        bucket["points"] += credits * result.grade_point
        bucket["courses"].append(result)
    for bucket in semesters.values():
        bucket["gpa"] = (bucket["points"] / bucket["credits"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if bucket["credits"] else Decimal("0")
    total_credits = sum((bucket["credits"] for bucket in semesters.values()), Decimal("0"))
    total_points = sum((bucket["points"] for bucket in semesters.values()), Decimal("0"))
    return {"semesters": list(semesters.values()), "cgpa": (total_points / total_credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_credits else Decimal("0")}


def transcript_code(student, results):
    snapshot = "|".join(f"{r.id}:{r.final_score}:{r.letter_grade}:{r.grade_point}" for r in results)
    snapshot_hash = hashlib.sha256(snapshot.encode()).hexdigest()
    verification = TranscriptVerification.objects.create(code=f"TR-{secrets.token_urlsafe(18)}", student=student, snapshot_hash=snapshot_hash)
    return verification, snapshot_hash
