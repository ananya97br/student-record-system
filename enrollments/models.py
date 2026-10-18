from django.conf import settings
from django.db import models


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        DROPPED = "DROPPED", "Dropped"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        COMPLETED = "COMPLETED", "Completed"

    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="enrollments")
    offering = models.ForeignKey("academic.CourseOffering", on_delete=models.PROTECT, related_name="enrollments")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ENROLLED, db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    dropped_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "offering"], name="unique_student_offering_enrollment")]
        indexes = [models.Index(fields=["student", "status"]), models.Index(fields=["offering", "status"])]
