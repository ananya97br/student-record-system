from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.crypto import EncryptedDecimalField


class AssessmentComponent(models.Model):
    class ComponentType(models.TextChoices):
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        QUIZ = "QUIZ", "Quiz"
        MIDTERM = "MIDTERM", "Midterm"
        FINAL = "FINAL", "Final exam"
        OTHER = "OTHER", "Other"

    offering = models.ForeignKey("academic.CourseOffering", on_delete=models.CASCADE, related_name="assessment_components")
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=20, choices=ComponentType.choices, default=ComponentType.OTHER)
    max_marks = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0.01)])
    weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["offering", "name"], name="unique_assessment_component_name")]


class GradeRecord(models.Model):
    component = models.ForeignKey(AssessmentComponent, on_delete=models.CASCADE, related_name="grade_records")
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="grade_records")
    mark = EncryptedDecimalField()
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entered_grades")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["component", "student"], name="unique_component_student_grade")]


class CourseResult(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="course_results")
    offering = models.ForeignKey("academic.CourseOffering", on_delete=models.PROTECT, related_name="course_results")
    final_score = EncryptedDecimalField(null=True)
    letter_grade = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_locked = models.BooleanField(default=False, db_index=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="locked_course_results")
    override_reason = models.CharField(max_length=500, blank=True)
    overridden_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="overridden_course_results")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "offering"], name="unique_student_offering_result")]
        indexes = [models.Index(fields=["student", "is_locked"]), models.Index(fields=["offering", "is_locked"])]


class TranscriptVerification(models.Model):
    code = models.CharField(max_length=80, unique=True, db_index=True)
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="transcript_verifications")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    generated_at = models.DateTimeField(auto_now_add=True)
    snapshot_hash = models.CharField(max_length=64)
