from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Student, StudentIdSequence


def next_student_id() -> str:
    year = timezone.now().year
    for _ in range(3):
        try:
            with transaction.atomic():
                sequence, created = StudentIdSequence.objects.get_or_create(year=year, defaults={"next_number": 2})
                if not created:
                    sequence = StudentIdSequence.objects.select_for_update().get(year=year)
                    number = sequence.next_number
                    sequence.next_number += 1
                    sequence.save(update_fields=["next_number"])
                else:
                    number = 1
                return f"STU-{year}-{number:04d}"
        except IntegrityError:
            continue
    # The unique constraint remains the final guard if a database cannot lock
    # a missing counter row concurrently.
    last = Student.objects.filter(student_id__startswith=f"STU-{year}-").order_by("-student_id").first()
    number = int(last.student_id.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"STU-{year}-{number:04d}"
