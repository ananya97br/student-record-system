from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from core.crypto import EncryptedTextField


class StudentIdSequence(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    next_number = models.PositiveIntegerField(default=1)


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        GRADUATED = "GRADUATED", "Graduated"
        SUSPENDED = "SUSPENDED", "Suspended"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    program = models.ForeignKey("academic.Program", on_delete=models.PROTECT, related_name="students")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = EncryptedTextField(blank=True)
    address = EncryptedTextField(blank=True)
    emergency_contact_name = EncryptedTextField(blank=True)
    emergency_contact_phone = EncryptedTextField(blank=True)
    national_identifier = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student_id"]
        indexes = [models.Index(fields=["program", "status"])]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.student_id} — {self.full_name}"


class ProfileChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Field(models.TextChoices):
        PHONE = "phone", "Phone"
        ADDRESS = "address", "Address"
        EMERGENCY_CONTACT_NAME = "emergency_contact_name", "Emergency contact name"
        EMERGENCY_CONTACT_PHONE = "emergency_contact_phone", "Emergency contact phone"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="profile_change_requests")
    field = models.CharField(max_length=40, choices=Field.choices)
    old_value = EncryptedTextField(blank=True)
    new_value = EncryptedTextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_profile_changes")
    review_reason = models.CharField(max_length=500, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["student", "status"])]


class StudentDocument(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CLEAN = "CLEAN", "Clean"
        INFECTED = "INFECTED", "Infected"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="documents")
    original_name = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=255, unique=True)
    content_type = models.CharField(max_length=100)
    extension = models.CharField(max_length=10)
    size_bytes = models.PositiveIntegerField()
    checksum_sha256 = models.CharField(max_length=64)
    scan_status = models.CharField(max_length=12, choices=ScanStatus.choices, default=ScanStatus.PENDING, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    scanned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["student", "scan_status"])]
