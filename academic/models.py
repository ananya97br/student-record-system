from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Program(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    duration_semesters = models.PositiveSmallIntegerField(default=8, validators=[MinValueValidator(1)])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Semester(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    add_drop_deadline = models.DateTimeField()
    is_current = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["is_current", "is_active"])]

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credits = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    programs = models.ManyToManyField(Program, related_name="courses", blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        indexes = [models.Index(fields=["code", "active"])]

    def __str__(self):
        return f"{self.code} — {self.title}"


class CoursePrerequisite(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="prerequisite_links")
    prerequisite = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="required_for_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "prerequisite"], name="unique_course_prerequisite")]


class FacultyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="faculty_profile")
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.employee_id} — {self.display_name}"


class CourseOffering(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        COMPLETED = "COMPLETED", "Completed"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="offerings")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="offerings")
    faculty = models.ForeignKey(FacultyProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name="offerings")
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    seats_available = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN, db_index=True)
    room = models.CharField(max_length=80, blank=True)
    schedule = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "semester"], name="unique_course_semester_offering")]
        indexes = [models.Index(fields=["semester", "status"]), models.Index(fields=["faculty", "semester"])]

    def __str__(self):
        return f"{self.course.code} / {self.semester.code}"


class GradingScheme(models.Model):
    name = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1)
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "version"], name="unique_grading_scheme_version")]


class GradeBand(models.Model):
    scheme = models.ForeignKey(GradingScheme, on_delete=models.CASCADE, related_name="bands")
    minimum_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))])
    maximum_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))])
    letter = models.CharField(max_length=5)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        ordering = ["-minimum_score"]
        constraints = [models.UniqueConstraint(fields=["scheme", "letter"], name="unique_scheme_letter")]


class FeeStructure(models.Model):
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="fee_structures")
    semester = models.ForeignKey(Semester, null=True, blank=True, on_delete=models.PROTECT, related_name="fee_structures")
    version = models.PositiveIntegerField(default=1)
    base_fee = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    per_credit_fee = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    currency = models.CharField(max_length=3, default="INR")
    active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["program", "semester", "version"], name="unique_fee_structure_version")]
        indexes = [models.Index(fields=["program", "active"])]


class Scholarship(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.PROTECT, related_name="scholarships")
    semester = models.ForeignKey(Semester, null=True, blank=True, on_delete=models.PROTECT, related_name="scholarships")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))])
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0"))])
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(percentage__isnull=False) | models.Q(amount__isnull=False)), name="scholarship_has_discount")]
