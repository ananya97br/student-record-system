from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from academic.models import FeeStructure, Scholarship
from core.audit import audit
from core.crypto import lookup_hash
from core.notifications import notify

from .models import Invoice, InvoiceLine, Payment, Receipt


def _payload_bytes(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class MockPaymentGateway:
    def sign(self, payload: dict) -> str:
        return hmac.new(settings.PAYMENT_MOCK_HMAC_SECRET.encode(), _payload_bytes(payload), hashlib.sha256).hexdigest()

    def checkout_url(self, payment):
        return f"{settings.APP_BASE_URL.rstrip('/')}/payment/mock/{payment.pk}"


def fee_structure_for(student, semester):
    return FeeStructure.objects.filter(program=student.program, active=True).filter(semester=semester).order_by("-version").first() or FeeStructure.objects.filter(program=student.program, active=True, semester__isnull=True).order_by("-version").first()


def best_scholarship(student, semester, subtotal):
    candidates = Scholarship.objects.filter(active=True).filter(program__isnull=True) | Scholarship.objects.filter(active=True, program=student.program)
    candidates = candidates.filter(semester__isnull=True) | candidates.filter(semester=semester)
    best = Decimal("0")
    for scholarship in candidates.distinct():
        discount = subtotal * (scholarship.percentage / Decimal("100")) if scholarship.percentage is not None else (scholarship.amount or Decimal("0"))
        best = max(best, discount)
    return min(best.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), subtotal)


def generate_invoice(student, semester):
    from enrollments.models import Enrollment

    existing = Invoice.objects.filter(student=student, semester=semester).first()
    if existing:
        return existing
    fee = fee_structure_for(student, semester)
    if not fee:
        raise ValueError("No fee structure is configured for this program and semester")
    credits = sum(enrollment.offering.course.credits for enrollment in Enrollment.objects.select_related("offering__course").filter(student=student, offering__semester=semester, status=Enrollment.Status.ENROLLED))
    base = fee.base_fee
    credit_fee = fee.per_credit_fee * credits
    subtotal = base + credit_fee
    discount = best_scholarship(student, semester, subtotal)
    total = max(Decimal("0"), subtotal - discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    invoice = Invoice.objects.create(student=student, semester=semester, invoice_number=f"INV-{timezone.now().year}-{secrets.token_hex(5).upper()}", base_fee=base, credit_fee=credit_fee, scholarship_discount=discount, subtotal=subtotal, total=total, balance=total, currency=fee.currency, status=Invoice.Status.UNPAID, due_date=semester.end_date)
    InvoiceLine.objects.create(invoice=invoice, description="Semester base fee", quantity=1, unit_price=base, line_total=base)
    if credits:
        InvoiceLine.objects.create(invoice=invoice, description=f"Course credits ({credits})", quantity=credits, unit_price=fee.per_credit_fee, line_total=credit_fee)
    if discount:
        InvoiceLine.objects.create(invoice=invoice, description="Best eligible scholarship", quantity=1, unit_price=-discount, line_total=-discount)
    return invoice


def initiate_payment(request, invoice, idempotency_key):
    if not idempotency_key:
        raise ValueError("Idempotency-Key is required")
    prior = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if prior:
        return prior
    if invoice.balance <= 0 or invoice.status == Invoice.Status.PAID:
        raise ValueError("Invoice has no outstanding balance")
    reference = f"PAY-{secrets.token_hex(9).upper()}"
    order = f"MOCK-{secrets.token_hex(9).upper()}"
    payment = Payment.objects.create(invoice=invoice, payment_reference=reference, gateway_order_reference=order, amount=invoice.balance, currency=invoice.currency, idempotency_key=idempotency_key, status=Payment.Status.PENDING)
    invoice.status = Invoice.Status.PENDING
    invoice.save(update_fields=["status", "updated_at"])
    audit(request, "PAYMENT_INITIATED", "Payment", payment.pk, {"invoiceId": invoice.id, "amount": str(payment.amount)})
    return payment


def process_callback(request, payload: dict, signature: str):
    gateway = MockPaymentGateway()
    expected = gateway.sign(payload)
    if not signature or not hmac.compare_digest(signature, expected):
        return None, "BAD_SIGNATURE"
    required = {"paymentReference", "gatewayOrderReference", "amount", "currency", "status"}
    if not required.issubset(payload):
        return None, "INVALID_PAYLOAD"
    payment = Payment.objects.select_related("invoice__student__user").filter(payment_reference_hash=lookup_hash(str(payload["paymentReference"]))).first()
    if not payment:
        return None, "UNKNOWN_REFERENCE"
    try:
        amount = Decimal(str(payload["amount"]))
    except Exception:
        return None, "REFERENCE_OR_AMOUNT_MISMATCH"
    if payment.gateway_order_reference != str(payload["gatewayOrderReference"]) or payment.currency != str(payload["currency"]) or amount != payment.amount:
        return None, "REFERENCE_OR_AMOUNT_MISMATCH"
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("invoice__student__user").get(pk=payment.pk)
        if payment.status in {Payment.Status.SUCCESS, Payment.Status.FAILED, Payment.Status.CANCELLED}:
            return payment, "ALREADY_PROCESSED"
        status = str(payload["status"])
        if status not in {Payment.Status.SUCCESS, Payment.Status.FAILED, Payment.Status.CANCELLED}:
            return None, "INVALID_STATUS"
        payment.status = status
        payment.provider_payload = {"status": status, "gatewayOrderReference": str(payload["gatewayOrderReference"]), "processedAt": timezone.now().isoformat()}
        if status == Payment.Status.SUCCESS:
            payment.paid_at = timezone.now()
            invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
            invoice.balance = max(Decimal("0"), invoice.balance - payment.amount)
            invoice.status = Invoice.Status.PAID if invoice.balance == 0 else Invoice.Status.PARTIAL
            invoice.save(update_fields=["balance", "status", "updated_at"])
            payment.save(update_fields=["status", "provider_payload", "paid_at", "updated_at"])
            Receipt.objects.get_or_create(payment=payment, defaults={"receipt_number": f"REC-{timezone.now().year}-{secrets.token_hex(5).upper()}"})
            audit(request, "PAYMENT_SUCCESS", "Payment", payment.pk, {"invoiceId": invoice.id, "amount": str(payment.amount)})
            transaction.on_commit(lambda: notify(payment.invoice.student.user, "Payment receipt", "Your payment was completed. A receipt is available in the student portal.", safe_metadata={"paymentId": str(payment.pk)}))
        else:
            payment.save(update_fields=["status", "provider_payload", "updated_at"])
            invoice = Invoice.objects.get(pk=payment.invoice_id)
            if invoice.status == Invoice.Status.PENDING:
                invoice.status = Invoice.Status.UNPAID
                invoice.save(update_fields=["status", "updated_at"])
            audit(request, f"PAYMENT_{status}", "Payment", payment.pk, {"invoiceId": invoice.id})
    return payment, "PROCESSED"
