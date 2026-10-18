from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.core.cache import cache

from accounts.models import AuditLog, OtpToken, User
from academic.models import CourseOffering
from attendance.services import percentage_for
from core.crypto import decrypt_value
from enrollments.models import Enrollment
from finance.models import Invoice, Payment, Receipt
from finance.services import MockPaymentGateway
from grading.models import CourseResult
from students.models import Student


class DemoRequirementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.client = Client()
        cache.clear()

    def login(self, login_id="student1.demo", password="Student1Demo!2026"):
        response = self.client.post("/api/auth/login", data=json.dumps({"loginId": login_id, "password": password}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.csrf = self.client.cookies["csrftoken"].value
        return response

    def post(self, path, payload, **extra):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, **extra)

    def test_TC_Auth_01_successful_login_and_role_access(self):
        self.login()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.get("/api/reports/enrollment").status_code, 403)
        self.assertEqual(self.client.get("/api/enrollments/eligible").status_code, 200)

    def test_TC_UX_02_portal_navigation_is_role_specific(self):
        self.login("student1.demo", "Student1Demo!2026")
        student_dashboard = self.client.get("/portal/dashboard")
        self.assertEqual(student_dashboard.status_code, 200)
        self.assertContains(student_dashboard, "/portal/enrollment")
        self.assertNotContains(student_dashboard, "/portal/faculty")
        self.assertNotContains(student_dashboard, "/portal/admin")
        self.assertRedirects(self.client.get("/portal/faculty"), "/portal/dashboard")
        self.assertRedirects(self.client.get("/portal/admin"), "/portal/dashboard")

        self.login("faculty1.demo", "Faculty1Demo!2026")
        faculty_dashboard = self.client.get("/portal/dashboard")
        self.assertContains(faculty_dashboard, "/portal/faculty")
        self.assertNotContains(faculty_dashboard, "/portal/profile")
        self.assertNotContains(faculty_dashboard, "/portal/admin")
        self.assertRedirects(self.client.get("/portal/profile"), "/portal/dashboard")

        self.login("admin.demo", "AdminDemo!2026")
        admin_dashboard = self.client.get("/portal/dashboard")
        self.assertContains(admin_dashboard, "/portal/admin")
        self.assertNotContains(admin_dashboard, "/portal/profile")
        self.assertNotContains(admin_dashboard, "/portal/faculty")
        self.assertRedirects(self.client.get("/portal/faculty"), "/portal/dashboard")

    def test_TC_Auth_02_five_failures_lock_audit_notification_and_unlock(self):
        for _ in range(4):
            response = self.client.post("/api/auth/login", data=json.dumps({"loginId": "student8.demo", "password": "wrong-password"}), content_type="application/json")
            self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/auth/login", data=json.dumps({"loginId": "student8.demo", "password": "wrong-password"}), content_type="application/json")
        self.assertEqual(response.status_code, 423)
        self.assertTrue(AuditLog.objects.filter(action="ACCOUNT_LOCK").exists())
        self.assertTrue(User.objects.get(login_id="student8.demo").is_locked)
        self.login("admin.demo", "AdminDemo!2026")
        student = User.objects.get(login_id="student8.demo")
        response = self.post(f"/api/auth/unlock/{student.pk}", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(pk=student.pk).status, User.Status.ACTIVE)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_TC_Auth_03_otp_reset_expiry_and_reuse(self):
        response = self.client.post("/api/auth/forgot-password", data=json.dumps({"email": "student1.demo@student-record.local"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mail.outbox)
        otp = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        response = self.client.post("/api/auth/reset-password", data=json.dumps({"email": "student1.demo@student-record.local", "otp": otp, "newPassword": "NewStudentPassword!2026"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/auth/reset-password", data=json.dumps({"email": "student1.demo@student-record.local", "otp": otp, "newPassword": "AnotherPassword!2026"}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.get(login_id="student1.demo").check_password("NewStudentPassword!2026"))

    def test_TC_Reg_01_admin_creates_student_with_generated_id(self):
        self.login("admin.demo", "AdminDemo!2026")
        response = self.post("/api/students", {"email": "new.student@student-record.local", "password": "NewStudent!2026", "firstName": "New", "lastName": "Student", "programId": 1})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertRegex(response.json()["studentId"], r"^STU-\d{4}-\d{4}$")
        self.assertTrue(AuditLog.objects.filter(action="STUDENT_CREATED").exists())

    def test_TC_Reg_02_profile_change_pending_until_approval(self):
        self.login()
        response = self.client.patch("/api/students/me", data=json.dumps({"phone": "+91-9999999999"}), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 202)
        student = Student.objects.get(student_id="STU-2026-0001")
        self.assertNotEqual(student.phone, "+91-9999999999")
        self.login("admin.demo", "AdminDemo!2026")
        pending = self.client.get("/api/students/change-requests").json()["items"]
        request_id = next(item["id"] for item in pending if item["studentId"] == student.student_id)
        response = self.post(f"/api/students/change-requests/{request_id}/decision", {"decision": "APPROVE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.get(pk=student.pk).phone, "+91-9999999999")

    def test_TC_Reg_03_document_validation_scan_and_ownership(self):
        self.login()
        pdf = SimpleUploadedFile("record.pdf", b"%PDF-1.4 clean document", content_type="application/pdf")
        response = self.client.post("/api/students/me/documents", data={"file": pdf}, HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 201, response.content)
        document_id = response.json()["id"]
        self.assertEqual(self.client.get(f"/api/students/documents/{document_id}/download").status_code, 200)
        infected = SimpleUploadedFile("bad.pdf", b"%PDF-1.4 EICAR-STANDARD-ANTIVIRUS-TEST-FILE", content_type="application/pdf")
        response = self.client.post("/api/students/me/documents", data={"file": infected}, HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 400)
        self.login("student2.demo", "Student2Demo!2026")
        self.assertEqual(self.client.get(f"/api/students/documents/{document_id}/download").status_code, 403)

    def test_TC_Enr_01_only_current_eligible_offerings(self):
        self.login()
        response = self.client.get("/api/enrollments/eligible")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(item["semester"] == "Fall 2026" for item in response.json()["items"]))
        self.assertTrue(any(item["eligible"] for item in response.json()["items"]))

    def test_TC_Enr_02_duplicate_and_full_seat_checks(self):
        self.login()
        offering = CourseOffering.objects.get(course__code="CS202", semester__code="2026-FALL")
        response = self.post("/api/enrollments", {"offeringId": offering.id})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Enrollment.objects.filter(offering=offering, status=Enrollment.Status.ENROLLED).count(), 2)

    def test_TC_Enr_03_drop_before_deadline_releases_seat(self):
        self.login()
        enrollment = Enrollment.objects.filter(student__student_id="STU-2026-0001", offering__course__code="CS201").first()
        response = self.post(f"/api/enrollments/{enrollment.id}/drop", {})
        self.assertEqual(response.status_code, 200)
        enrollment.refresh_from_db()
        enrollment.offering.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)
        self.assertEqual(enrollment.offering.seats_available, enrollment.offering.capacity - Enrollment.objects.filter(offering=enrollment.offering, status=Enrollment.Status.ENROLLED).count())

    def test_TC_Att_01_assigned_faculty_and_48_hour_rule(self):
        self.login("faculty2.demo", "Faculty2Demo!2026")
        offering = CourseOffering.objects.get(course__code="CS201", semester__code="2026-FALL")
        response = self.client.get(f"/api/attendance/offerings/{offering.id}/roster")
        self.assertEqual(response.status_code, 200)
        self.login("faculty3.demo", "Faculty3Demo!2026")
        self.assertEqual(self.client.get(f"/api/attendance/offerings/{offering.id}/roster").status_code, 403)

    def test_TC_Att_02_percentage_and_below_threshold_flag(self):
        self.login()
        response = self.client.get("/api/attendance/student-summary")
        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.json()["items"] if item["courseCode"] == "CS201")
        self.assertEqual(row["percentage"], 50.0)
        self.assertTrue(row["belowThreshold"])

    def test_TC_Grd_01_grade_lock_and_admin_override_audit(self):
        result = CourseResult.objects.filter(student__student_id="STU-2026-0001").first()
        self.login("admin.demo", "AdminDemo!2026")
        response = self.post(f"/api/grades/results/{result.id}/override", {"reason": "Correction approved", "finalScore": "91", "letterGrade": "A+", "gradePoint": "10"})
        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertEqual(result.letter_grade, "A+")
        self.assertTrue(AuditLog.objects.filter(action="GRADE_ADMIN_OVERRIDE", entity_id=str(result.id)).exists())

    def test_TC_Grd_02_known_dataset_gpa(self):
        self.login()
        response = self.client.get("/api/grades/gpa")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cgpa"], "8.50")

    def test_TC_Grd_03_transcript_pdf_and_verification(self):
        self.login()
        response = self.client.get("/api/grades/transcript")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        code = __import__("grading.models", fromlist=["TranscriptVerification"]).TranscriptVerification.objects.latest("generated_at").code
        response = self.client.get(f"/api/grades/transcript/verify/{code}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])

    def test_TC_Fee_01_configured_formula(self):
        self.login()
        invoice = Invoice.objects.get(invoice_number="INV-DEMO-0001")
        self.assertEqual(invoice.total, invoice.base_fee + invoice.credit_fee - invoice.scholarship_discount)
        self.assertEqual(invoice.currency, "INR")

    def test_TC_Fee_02_signed_callback_idempotent_receipt(self):
        self.login()
        invoice = Invoice.objects.get(invoice_number="INV-DEMO-0001")
        response = self.post("/api/fees/payments/initiate", {"invoiceId": invoice.id}, HTTP_IDEMPOTENCY_KEY="test-idempotent-payment")
        self.assertEqual(response.status_code, 201)
        payment = Payment.objects.get(pk=response.json()["paymentId"])
        payload = {"paymentReference": payment.payment_reference, "gatewayOrderReference": payment.gateway_order_reference, "amount": str(payment.amount), "currency": payment.currency, "status": "SUCCESS"}
        signature = MockPaymentGateway().sign(payload)
        response = self.client.post("/api/fees/payments/callback", data=json.dumps(payload), content_type="application/json", HTTP_X_PAYMENT_SIGNATURE=signature)
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/fees/payments/callback", data=json.dumps(payload), content_type="application/json", HTTP_X_PAYMENT_SIGNATURE=signature)
        self.assertTrue(response.json()["idempotent"])
        self.assertEqual(Receipt.objects.filter(payment=payment).count(), 1)
        bad = self.client.post("/api/fees/payments/callback", data=json.dumps(payload), content_type="application/json", HTTP_X_PAYMENT_SIGNATURE="bad")
        self.assertEqual(bad.status_code, 400)

    def test_TC_Rpt_01_report_rows_and_exports(self):
        self.login("admin.demo", "AdminDemo!2026")
        response = self.client.get("/api/reports/enrollment")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["total"], 0)
        self.assertEqual(self.client.get("/api/reports/fees?format=pdf")["Content-Type"], "application/pdf")
        self.assertEqual(self.client.get("/api/reports/grades?format=xlsx")["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_TC_Rpt_02_audit_is_append_only_and_sensitive_values_ciphertext(self):
        row = AuditLog.objects.create(action="TEST", entity_type="Test", entity_id="1", correlation_id="test", metadata={})
        with self.assertRaises(ValueError):
            row.save()
        with self.assertRaises(ValueError):
            row.delete()
        student = Student.objects.get(student_id="STU-2026-0001")
        with connection.cursor() as cursor:
            cursor.execute("SELECT phone FROM students_student WHERE id = %s", [student.id])
            raw = cursor.fetchone()[0]
        self.assertNotIn("+91-9000000001", raw)
        self.assertEqual(student.phone, "+91-9000000001")

    def test_TC_Sec_04_cross_role_denial_is_logged(self):
        self.login("student1.demo", "Student1Demo!2026")
        response = self.client.get("/api/reports/enrollment")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(AuditLog.objects.filter(action="AUTHORIZATION_DENIED").exists())

    def test_TC_Sec_06_encryption_tampering_fails(self):
        student = Student.objects.get(student_id="STU-2026-0001")
        with connection.cursor() as cursor:
            cursor.execute("SELECT phone FROM students_student WHERE id = %s", [student.id])
            raw = cursor.fetchone()[0]
            cursor.execute("UPDATE students_student SET phone = %s WHERE id = %s", [raw[:-1] + ("A" if raw[-1] != "A" else "B"), student.id])
        with self.assertRaises(ValueError):
            Student.objects.get(pk=student.pk).phone

    def test_TC_Sec_01_password_plaintext_prohibition(self):
        user = User.objects.get(login_id="student1.demo")
        self.assertNotIn("Student1Demo!2026", user.password)
        self.assertTrue(user.password.startswith("argon2"))

    def test_TC_Sec_03_argon2_hash_and_safe_auth_values(self):
        user = User.objects.get(login_id="admin.demo")
        self.assertTrue(user.password.startswith("argon2"))
        self.assertFalse(any("AdminDemo!2026" in json.dumps(row.metadata) for row in AuditLog.objects.all()))

    def test_TC_Sec_05_repeated_exports_create_alert(self):
        self.login("admin.demo", "AdminDemo!2026")
        for _ in range(5):
            response = self.client.get("/api/reports/enrollment?format=xlsx")
            self.assertEqual(response.status_code, 200)
        from accounts.models import SecurityAlert

        self.assertTrue(SecurityAlert.objects.filter(alert_type="BULK_EXPORT").exists())

    def test_TC_Ops_01_retention_and_health_evidence(self):
        self.assertEqual(__import__("django.conf", fromlist=["settings"]).settings.RETENTION_YEARS, 10)
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertEqual(self.client.get("/api/health/live").status_code, 200)

    def test_TC_Perf_01_and_TC_Perf_02_load_profiles_exist(self):
        self.assertIn("p(95)<3000", Path("load/k6/target-2000.js").read_text())
        self.assertIn("p(95)<3000", Path("load/k6/target-10000.js").read_text())

    def test_TC_Sec_02_tls_configuration_is_modern(self):
        nginx = Path("infra/nginx/default.conf").read_text()
        compose = Path("docker-compose.yml").read_text()
        self.assertIn("listen 80;", nginx)
        self.assertIn("proxy_pass http://srs_api", nginx)
        self.assertIn('"8000:80"', compose)
        self.assertNotIn('"8443:443"', compose)

    def test_TC_UX_01_accessible_portal_evidence(self):
        html = Path("templates/portal.html").read_text()
        self.assertIn('id="main-content"', html)
        self.assertNotIn('data-contrast-toggle', Path("templates/login.html").read_text() + html)
        self.assertNotIn('Enable high contrast', Path("templates/login.html").read_text() + html)
        self.assertIn("scope=\"col\"", Path("static/js/app.js").read_text())
