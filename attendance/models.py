from django.conf import settings
from django.db import models


class AttendanceSession(models.Model):
    offering = models.ForeignKey("academic.CourseOffering", on_delete=models.PROTECT, related_name="attendance_sessions")
    session_at = models.DateTimeField(db_index=True)
    topic = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_attendance_sessions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-session_at"]
        constraints = [models.UniqueConstraint(fields=["offering", "session_at"], name="unique_offering_attendance_session")]


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        LATE = "LATE", "Late"
        ABSENT = "ABSENT", "Absent"
        EXCUSED = "EXCUSED", "Excused"

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=Status.choices)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="marked_attendance")
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_session_student_attendance")]
        indexes = [models.Index(fields=["student", "status"]), models.Index(fields=["session", "student"])]
