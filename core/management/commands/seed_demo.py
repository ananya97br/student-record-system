"""Seed the deterministic data used by local development and automated tests."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from academic.models import (
    Course,
    CourseOffering,
    FacultyProfile,
    FeeStructure,
    GradeBand,
    GradingScheme,
    Program,
    Semester,
)
from attendance.models import AttendanceRecord, AttendanceSession
from core.models import SystemConfig
from enrollments.models import Enrollment
from finance.models import Invoice, InvoiceLine
from grading.models import CourseResult
from students.models import Student, StudentIdSequence


DEMO_PASSWORDS = {
    "student1.demo": "Student1Demo!2026",
    "student2.demo": "Student2Demo!2026",
    "student8.demo": "Student8Demo!2026",
}


class Command(BaseCommand):
    help = "Create the deterministic demo records used by the application and tests."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate()

        program = self._seed_program()
        semester = self._seed_semester(now, today)
        users = self._seed_users()
        students = self._seed_students(users, program)
        faculty = self._seed_faculty(users)
        courses = self._seed_courses(program)
        offerings = self._seed_offerings(courses, semester, faculty)
        self._seed_enrollments(students, offerings)
        self._seed_attendance(students["student1.demo"], offerings["CS201"], faculty["faculty2.demo"], today)
        self._seed_grading(students["student1.demo"], offerings, faculty["faculty2.demo"].user, now)
        self._seed_finance(students["student1.demo"], semester)
        self._seed_configuration()
        self._seed_student_sequence(today.year, students)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    @staticmethod
    def _seed_program() -> Program:
        program, _ = Program.objects.update_or_create(
            code="BTECH",
            defaults={
                "name": "Bachelor of Technology in Computer Science",
                "duration_semesters": 8,
                "active": True,
            },
        )
        return program

    @staticmethod
    def _seed_semester(now, today) -> Semester:
        # Keep the fixture's public name/code stable while making its date range
        # usable when the command is run outside the original demo year.
        start_date = min(date(2026, 1, 1), today)
        end_date = max(date(2026, 12, 31), today + timedelta(days=365))
        semester, _ = Semester.objects.update_or_create(
            code="2026-FALL",
            defaults={
                "name": "Fall 2026",
                "start_date": start_date,
                "end_date": end_date,
                "add_drop_deadline": now + timedelta(days=30),
                "is_current": True,
                "is_active": True,
            },
        )
        Semester.objects.exclude(pk=semester.pk).update(is_current=False)
        return semester

    @staticmethod
    def _seed_users() -> dict[str, User]:
        definitions = {
            "admin.demo": ("admin.demo@student-record.local", "AdminDemo!2026", User.Role.ADMIN),
            "faculty1.demo": ("faculty1.demo@student-record.local", "Faculty1Demo!2026", User.Role.FACULTY),
            "faculty2.demo": ("faculty2.demo@student-record.local", "Faculty2Demo!2026", User.Role.FACULTY),
            "faculty3.demo": ("faculty3.demo@student-record.local", "Faculty3Demo!2026", User.Role.FACULTY),
            "student1.demo": ("student1.demo@student-record.local", DEMO_PASSWORDS["student1.demo"], User.Role.STUDENT),
            "student2.demo": ("student2.demo@student-record.local", DEMO_PASSWORDS["student2.demo"], User.Role.STUDENT),
            "student8.demo": ("student8.demo@student-record.local", DEMO_PASSWORDS["student8.demo"], User.Role.STUDENT),
        }
        users = {}
        for login_id, (email, password, role) in definitions.items():
            user, _ = User.objects.get_or_create(login_id=login_id, defaults={"email": email})
            user.email = email
            user.role = role
            user.status = User.Status.ACTIVE
            user.is_active = True
            user.is_staff = role in {User.Role.ADMIN, User.Role.SYSADMIN}
            user.is_superuser = role == User.Role.SYSADMIN
            user.failed_login_attempts = 0
            user.locked_at = None
            user.set_password(password)
            user.save()
            users[login_id] = user
        return users

    @staticmethod
    def _seed_students(users: dict[str, User], program: Program) -> dict[str, Student]:
        students = {}
        for number in (1, 2, 8):
            login_id = f"student{number}.demo"
            student, _ = Student.objects.update_or_create(
                user=users[login_id],
                defaults={
                    "student_id": f"STU-2026-{number:04d}",
                    "program": program,
                    "status": Student.Status.ACTIVE,
                    "first_name": "Demo",
                    "last_name": f"Student {number}",
                    "phone": f"+91-900000000{number}",
                    "address": "Demo address",
                    "emergency_contact_name": "Demo Contact",
                    "emergency_contact_phone": f"+91-911111111{number}",
                    "national_identifier": f"DEMO-NID-{number}",
                },
            )
            students[login_id] = student
        return students

    @staticmethod
    def _seed_faculty(users: dict[str, User]) -> dict[str, FacultyProfile]:
        definitions = {
            "faculty1.demo": ("FAC-001", "Computer Science", "Dr. Demo One"),
            "faculty2.demo": ("FAC-002", "Computer Science", "Dr. Demo Two"),
            "faculty3.demo": ("FAC-003", "Mathematics", "Dr. Demo Three"),
        }
        faculty = {}
        for login_id, (employee_id, department, display_name) in definitions.items():
            profile, _ = FacultyProfile.objects.update_or_create(
                user=users[login_id],
                defaults={"employee_id": employee_id, "department": department, "display_name": display_name},
            )
            faculty[login_id] = profile
        return faculty

    @staticmethod
    def _seed_courses(program: Program) -> dict[str, Course]:
        definitions = {
            "CS201": ("Data Structures", 3),
            "CS202": ("Database Systems", 3),
            "CS203": ("Software Engineering", 3),
        }
        courses = {}
        for code, (title, credits) in definitions.items():
            course, _ = Course.objects.update_or_create(
                code=code,
                defaults={"title": title, "credits": credits, "active": True},
            )
            course.programs.set([program])
            courses[code] = course
        return courses

    @staticmethod
    def _seed_offerings(courses, semester, faculty):
        definitions = {
            "CS201": (faculty["faculty2.demo"], 3, "A-101", "Mon/Wed 10:00"),
            "CS202": (faculty["faculty1.demo"], 2, "A-102", "Tue/Thu 11:00"),
            "CS203": (faculty["faculty3.demo"], 3, "A-103", "Fri 09:00"),
        }
        offerings = {}
        for code, (assigned_faculty, capacity, room, schedule) in definitions.items():
            offering, _ = CourseOffering.objects.update_or_create(
                course=courses[code],
                semester=semester,
                defaults={
                    "faculty": assigned_faculty,
                    "capacity": capacity,
                    "seats_available": capacity,
                    "status": CourseOffering.Status.OPEN,
                    "room": room,
                    "schedule": schedule,
                },
            )
            offerings[code] = offering
        return offerings

    @staticmethod
    def _seed_enrollments(students, offerings):
        enrolled = {
            "CS201": ("student1.demo", "student2.demo"),
            "CS202": ("student1.demo", "student2.demo"),
        }
        for course_code, logins in enrolled.items():
            offering = offerings[course_code]
            for login_id in logins:
                Enrollment.objects.update_or_create(
                    student=students[login_id],
                    offering=offering,
                    defaults={"status": Enrollment.Status.ENROLLED, "dropped_at": None},
                )
            active_count = Enrollment.objects.filter(offering=offering, status=Enrollment.Status.ENROLLED).count()
            offering.seats_available = max(0, offering.capacity - active_count)
            offering.save(update_fields=["seats_available", "updated_at"])

    @staticmethod
    def _seed_attendance(student, offering, faculty, today):
        for offset, status in ((1, AttendanceRecord.Status.PRESENT), (2, AttendanceRecord.Status.ABSENT)):
            session_date = today - timedelta(days=offset)
            session_at = timezone.make_aware(datetime.combine(session_date, time(10, 0)))
            session, _ = AttendanceSession.objects.update_or_create(
                offering=offering,
                session_at=session_at,
                defaults={"topic": "Demo lecture", "created_by": faculty.user},
            )
            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={"status": status, "marked_by": faculty.user},
            )

    @staticmethod
    def _seed_grading(student, offerings, faculty, now):
        scheme, _ = GradingScheme.objects.update_or_create(
            name="Demo grading scheme",
            version=1,
            defaults={"is_default": True, "active": True},
        )
        GradingScheme.objects.exclude(pk=scheme.pk).update(is_default=False)
        bands = (
            ("A+", Decimal("90"), Decimal("100"), Decimal("10")),
            ("A", Decimal("80"), Decimal("89.99"), Decimal("9")),
            ("B+", Decimal("70"), Decimal("79.99"), Decimal("8")),
            ("B", Decimal("60"), Decimal("69.99"), Decimal("7")),
            ("C", Decimal("50"), Decimal("59.99"), Decimal("6")),
            ("F", Decimal("0"), Decimal("49.99"), Decimal("0")),
        )
        for letter, minimum, maximum, grade_point in bands:
            GradeBand.objects.update_or_create(
                scheme=scheme,
                letter=letter,
                defaults={"minimum_score": minimum, "maximum_score": maximum, "grade_point": grade_point},
            )

        results = {
            "CS201": (Decimal("75"), "B+", Decimal("8")),
            "CS202": (Decimal("85"), "A", Decimal("9")),
        }
        for course_code, (score, letter, grade_point) in results.items():
            CourseResult.objects.update_or_create(
                student=student,
                offering=offerings[course_code],
                defaults={
                    "final_score": score,
                    "letter_grade": letter,
                    "grade_point": grade_point,
                    "is_locked": True,
                    "finalized_at": now,
                    "locked_by": faculty,
                },
            )

    @staticmethod
    def _seed_finance(student, semester):
        invoice, _ = Invoice.objects.update_or_create(
            student=student,
            semester=semester,
            defaults={
                "invoice_number": "INV-DEMO-0001",
                "base_fee": Decimal("10000.00"),
                "credit_fee": Decimal("1500.00"),
                "scholarship_discount": Decimal("500.00"),
                "subtotal": Decimal("11500.00"),
                "total": Decimal("11000.00"),
                "balance": Decimal("11000.00"),
                "currency": "INR",
                "status": Invoice.Status.UNPAID,
                "due_date": semester.end_date,
            },
        )
        InvoiceLine.objects.update_or_create(
            invoice=invoice,
            description="Semester fees",
            defaults={"quantity": Decimal("1"), "unit_price": invoice.total, "line_total": invoice.total},
        )

    @staticmethod
    def _seed_configuration():
        SystemConfig.objects.update_or_create(
            key="attendance_threshold",
            defaults={"value": {"value": 75}, "description": "Minimum attendance percentage"},
        )
        SystemConfig.objects.update_or_create(
            key="retention_years",
            defaults={"value": {"value": 10}, "description": "Record retention period"},
        )

    @staticmethod
    def _seed_student_sequence(year, students):
        highest = max(
            (int(student.student_id.rsplit("-", 1)[-1]) for student in students.values() if student.student_id.startswith(f"STU-{year}-")),
            default=0,
        )
        sequence, _ = StudentIdSequence.objects.get_or_create(year=year, defaults={"next_number": highest + 1})
        if sequence.next_number <= highest:
            sequence.next_number = highest + 1
            sequence.save(update_fields=["next_number"])
