from __future__ import annotations

import json
from io import BytesIO

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import User
from academic.models import Semester
from core.audit import audit
from core.errors import error_response
from core.permissions import api_view, login_required, parse_json, roles
from students.models import Student

from .models import Invoice, Payment, Receipt
from .services import MockPaymentGateway, generate_invoice, initiate_payment, process_callback


def _invoice(invoice):
    return {"id": invoice.id, "number": invoice.invoice_number, "semester": invoice.semester.name, "baseFee": str(invoice.base_fee), "creditFee": str(invoice.credit_fee), "scholarship": str(invoice.scholarship_discount), "subtotal": str(invoice.subtotal), "total": str(invoice.total), "balance": str(invoice.balance), "currency": invoice.currency, "status": invoice.status, "generatedAt": invoice.generated_at.isoformat(), "lines": [{"description": line.description, "quantity": str(line.quantity), "unitPrice": str(line.unit_price), "total": str(line.line_total)} for line in invoice.lines.all()]}


@api_view(require_csrf=False)
@login_required
def invoices(request):
    if request.user.role == User.Role.STUDENT:
        student = Student.objects.filter(user=request.user).first()
        qs = Invoice.objects.select_related("semester").prefetch_related("lines").filter(student=student)
    elif request.user.role in {User.Role.ADMIN, User.Role.SYSADMIN}:
        qs = Invoice.objects.select_related("semester", "student").prefetch_related("lines")
    else:
        return error_response("FORBIDDEN", "Not authorized.", request.correlation_id, 403)
    return JsonResponse({"items": [_invoice(row) for row in qs[:500]]})


@csrf_exempt
@api_view()
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def generate(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    student = Student.objects.filter(pk=data.get("studentId")).first()
    semester = Semester.objects.filter(pk=data.get("semesterId")).first()
    if not student or not semester:
        return error_response("INVALID_INPUT", "studentId and semesterId are required.", request.correlation_id, 400)
    try:
        invoice = generate_invoice(student, semester)
    except ValueError as exc:
        return error_response("FEE_CONFIGURATION_MISSING", str(exc), request.correlation_id, 409)
    audit(request, "INVOICE_GENERATED", "Invoice", invoice.id, {"studentId": student.student_id})
    return JsonResponse(_invoice(invoice), status=201)


@api_view(require_csrf=False)
@login_required
def invoice_detail(request, invoice_id):
    invoice = Invoice.objects.select_related("student__user", "semester").prefetch_related("lines").filter(pk=invoice_id).first()
    if not invoice:
        return error_response("NOT_FOUND", "Invoice not found.", request.correlation_id, 404)
    if request.user.role == User.Role.STUDENT and invoice.student.user_id != request.user.pk:
        audit(request, "AUTHORIZATION_DENIED", "Invoice", invoice.id)
        return error_response("FORBIDDEN", "You are not authorized to view this invoice.", request.correlation_id, 403)
    if request.user.role not in {User.Role.STUDENT, User.Role.ADMIN, User.Role.SYSADMIN}:
        return error_response("FORBIDDEN", "Not authorized.", request.correlation_id, 403)
    return JsonResponse(_invoice(invoice))


@csrf_exempt
@api_view()
@login_required
def initiate_payment_view(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    data = parse_json(request) or {}
    invoice = Invoice.objects.select_related("student__user").filter(pk=data.get("invoiceId")).first()
    if not invoice:
        return error_response("NOT_FOUND", "Invoice not found.", request.correlation_id, 404)
    if request.user.role == User.Role.STUDENT and invoice.student.user_id != request.user.pk:
        audit(request, "AUTHORIZATION_DENIED", "Invoice", invoice.id)
        return error_response("FORBIDDEN", "You are not authorized to pay this invoice.", request.correlation_id, 403)
    key = request.headers.get("Idempotency-Key") or data.get("idempotencyKey")
    try:
        payment = initiate_payment(request, invoice, key)
    except ValueError as exc:
        return error_response("PAYMENT_NOT_ALLOWED", str(exc), request.correlation_id, 409)
    return JsonResponse({"paymentId": str(payment.pk), "reference": payment.payment_reference, "amount": str(payment.amount), "currency": payment.currency, "status": payment.status, "checkoutUrl": MockPaymentGateway().checkout_url(payment)}, status=201)


@csrf_exempt
@api_view(require_csrf=False)
def payment_callback(request):
    if request.method != "POST":
        return error_response("METHOD_NOT_ALLOWED", "POST is required.", request.correlation_id, 405)
    try:
        payload = json.loads(request.body or "{}")
    except ValueError:
        return error_response("INVALID_PAYLOAD", "JSON payload required.", request.correlation_id, 400)
    payment, result = process_callback(request, payload, request.headers.get("X-Payment-Signature", ""))
    if result == "BAD_SIGNATURE":
        return error_response("BAD_SIGNATURE", "Payment signature verification failed.", request.correlation_id, 400)
    if result == "UNKNOWN_REFERENCE":
        return error_response("UNKNOWN_REFERENCE", "Payment reference not found.", request.correlation_id, 404)
    if result in {"REFERENCE_OR_AMOUNT_MISMATCH", "INVALID_STATUS", "INVALID_PAYLOAD"}:
        return error_response(result, "Payment callback did not match a pending order.", request.correlation_id, 400)
    return JsonResponse({"acknowledged": True, "status": payment.status, "idempotent": result == "ALREADY_PROCESSED"})


@api_view(require_csrf=False)
@login_required
def payment_status(request, payment_id):
    payment = Payment.objects.select_related("invoice__student__user").filter(pk=payment_id).first()
    if not payment:
        return error_response("NOT_FOUND", "Payment not found.", request.correlation_id, 404)
    if request.user.role == User.Role.STUDENT and payment.invoice.student.user_id != request.user.pk:
        audit(request, "AUTHORIZATION_DENIED", "Payment", payment.pk)
        return error_response("FORBIDDEN", "Not authorized.", request.correlation_id, 403)
    return JsonResponse({"id": str(payment.pk), "reference": payment.payment_reference, "amount": str(payment.amount), "currency": payment.currency, "status": payment.status, "invoiceId": payment.invoice_id, "receiptId": payment.receipt.id if hasattr(payment, "receipt") else None})


@api_view(require_csrf=False)
@login_required
def receipt_pdf(request, receipt_id):
    receipt = Receipt.objects.select_related("payment__invoice__student__user", "payment__invoice").filter(pk=receipt_id).first()
    if not receipt:
        return error_response("NOT_FOUND", "Receipt not found.", request.correlation_id, 404)
    if request.user.role == User.Role.STUDENT and receipt.payment.invoice.student.user_id != request.user.pk:
        audit(request, "AUTHORIZATION_DENIED", "Receipt", receipt.id)
        return error_response("FORBIDDEN", "Not authorized.", request.correlation_id, 403)
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    student = receipt.payment.invoice.student
    flow = [Paragraph("Student Record System", styles["Title"]), Paragraph("Payment Receipt", styles["Heading2"]), Spacer(1, 16)]
    data = [["Receipt number", receipt.receipt_number], ["Student", f"{student.full_name} ({student.student_id})"], ["Invoice", receipt.payment.invoice.invoice_number], ["Payment reference", receipt.payment.payment_reference], ["Amount", f"{receipt.payment.amount} {receipt.payment.currency}"], ["Paid at", receipt.payment.paid_at.isoformat() if receipt.payment.paid_at else ""]]
    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e7eef4")), ("FONTSIZE", (0, 0), (-1, -1), 10)]))
    flow.append(table)
    doc.build(flow)
    audit(request, "RECEIPT_GENERATED", "Receipt", receipt.id)
    return HttpResponse(output.getvalue(), content_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="receipt.pdf"'})


@api_view(require_csrf=False)
@roles(User.Role.ADMIN, User.Role.SYSADMIN)
def reconciliation(request):
    pending = [{"id": str(p.pk), "reference": p.payment_reference, "amount": str(p.amount), "createdAt": p.created_at.isoformat()} for p in Payment.objects.filter(status=Payment.Status.PENDING).select_related("invoice")[:500]]
    return JsonResponse({"items": pending})
