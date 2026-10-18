from __future__ import annotations

import uuid

from django.db import models

from core.crypto import EncryptedTextField, lookup_hash


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PENDING = "PENDING", "Payment pending"
        PARTIAL = "PARTIAL", "Partially paid"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"

    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="invoices")
    semester = models.ForeignKey("academic.Semester", on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=40, unique=True)
    base_fee = models.DecimalField(max_digits=12, decimal_places=2)
    credit_fee = models.DecimalField(max_digits=12, decimal_places=2)
    scholarship_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.UNPAID, db_index=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "semester"], name="unique_student_semester_invoice")]
        indexes = [models.Index(fields=["student", "status"]), models.Index(fields=["semester", "status"])]


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    payment_reference = EncryptedTextField()
    payment_reference_hash = models.CharField(max_length=64, unique=True, db_index=True)
    gateway_order_reference = EncryptedTextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    idempotency_key = models.CharField(max_length=120, unique=True)
    provider_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.payment_reference:
            self.payment_reference_hash = lookup_hash(self.payment_reference)
        return super().save(*args, **kwargs)


class Receipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="receipt")
    receipt_number = models.CharField(max_length=40, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
