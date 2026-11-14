# Unit and Integration Testing Report

## Project and test scope

The Student Record System is a Django/Django REST Framework modular monolith. The unit and integration tests exercise real Django URLs, database transactions, seeded records, permission checks, encrypted fields, document validation, report exports, and business services. The executed areas were authentication, lockout, OTP reset, registration, approval, document security, enrollment, attendance, grades, GPA/CGPA, transcripts, fees, payment callbacks, reports, audit logging, password security, encryption, health checks, backup/restore, accessibility configuration, and browser navigation.

## Execution result

- Full pytest discovery: **74 passed, 0 failed, 0 errors, 0 skipped**.
- Command: `BASE_URL=http://127.0.0.1:8000 .venv/bin/pytest -q`.
- Duration: **11.945 seconds** under the final coverage/JUnit run.
- Canonical command: `.venv/bin/python manage.py test tests -v 2` -> **39 passed** in 3.680 seconds on SQLite.
- Canonical MySQL command: `docker compose -p srs-report exec -T api pytest tests -q --create-db` -> **39 passed**.
- Browser command: `BASE_URL=http://127.0.0.1:8000 .venv/bin/pytest e2e -q` -> **2 passed**.

## Test-area results

| Area | Test IDs | Result |
|---|---|---|
| Authentication/authorization | TC-Auth-01 to TC-Auth-03 | PASS |
| Registration/profile/documents | TC-Reg-01 to TC-Reg-03 | PASS |
| Enrollment/drop rules | TC-Enr-01, TC-Enr-02, TC-Enr-03/03a/03b | PASS |
| Attendance | TC-Att-01, TC-Att-02 | PASS |
| Grades/transcripts | TC-Grd-01, 01a-01g, 02, 03 | PASS |
| Fees/payments | TC-Fee-01, TC-Fee-02 | PASS |
| Reports/audit | TC-Rpt-01, TC-Rpt-02 | PASS |
| Security | TC-Sec-01 to TC-Sec-06 and password hashing | PASS |
| Operations/backup/UX/performance configuration | TC-Ops, TC-Perf, TC-UX and supplemental tests | PASS |
| Browser E2E/axe | `e2e/test_portal.py` | 2 PASS |

The test IDs and their actual outcomes are reproduced below so the report remains readable without opening another document.

| Test ID | Test objective | Actual result |
|---|---|---|
| TC-Auth-01 | Successful login and role access | PASS |
| TC-Auth-02 | Five failed logins lock account; audit/alert/notification and unlock | PASS |
| TC-Auth-03 | OTP password reset expiry and reuse rejection | PASS |
| TC-Reg-01/02/03 | Generated student ID, approval workflow, secure documents and ownership | PASS |
| TC-Enr-01/02/03/03a/03b | Eligibility, duplicate/full seats, deadline and repeat drop rules | PASS |
| TC-Att-01/02 | Assigned faculty authorization, attendance window, percentage and threshold | PASS |
| TC-Grd-01 series | Finalization lock, faculty restriction, reason-required override, rollback and audit | PASS |
| TC-Grd-02/03 | GPA dataset and transcript PDF/verification | PASS |
| TC-Fee-01/02 | Fee formula, valid/invalid callback, mismatch and idempotent receipt | PASS |
| TC-Rpt-01/02 | Report data/exports, append-only audit and ciphertext | PASS |
| TC-Sec-01-06 | Password, TLS, Argon2, role denial, export alert and tamper detection | PASS |
| TC-Ops-01/02/03 | Health/readiness, database-failure reporting, and backup/restore | PASS |
| TC-Perf-01/02 | k6 profile configuration exists | PASS for configuration; separate historical load thresholds FAILED |
| TC-UX-01/02 | Accessibility markup, browser login/navigation and role navigation | PASS |

The final JUnit inventory contained 74 executed entries: 39 canonical requirement tests, 33 supplemental root tests, and 2 Playwright browser tests. Every entry was PASS.

## Evidence

The tests cover positive and negative paths for lockout, OTP reuse, role denial,
document scanning/ownership, duplicate/full enrollment, drop deadlines, grade
locks and overrides, payment signatures/idempotency, audit immutability,
encryption tampering, health failure handling, backup/restore, accessibility
markup, and browser navigation.

## References and links

The preceding sections state what was tested, how it was tested, and the actual results. These links provide the source implementation and raw evidence for verification:

- [Student Record System repository](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo)
- [Canonical requirement tests](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/tests/test_requirements.py)
- [Password/security tests](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/tests/test_password_security.py)
- [Browser tests](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/e2e/test_portal.py)
- [Test traceability matrix](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/TEST_MATRIX.md)
- [JUnit result and raw logs](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo/docs/reports)
