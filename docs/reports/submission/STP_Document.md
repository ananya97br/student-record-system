# Software Test Plan (STP)

## 1. Project information

| Field | Value |
|---|---|
| Project | Student Record System |
| Version | 1.0.0 |
| Revision tested | `bf8cfd4` plus current working-tree changes |
| Environment | Linux x86_64, Python 3.14.4, Django 5.2.19 |
| Database | SQLite local/test database |
| Test tools | pytest 8.4.2, pytest-django, coverage.py 7.17.2, Django Test Framework, curl |

## 2. Purpose

This plan defines the verification approach for the Student Record System, a role-based Django application for student records, academic administration, enrollment, attendance, grading, fees, reporting, security, and auditing.

## 3. Project overview and architecture

The system is a modular monolith. A browser uses Django templates and vanilla JavaScript; Nginx is the public proxy in the container deployment; Django provides the portal and REST API; domain modules implement the business rules; and SQLite or MySQL stores the data.

| Role/module | Information verified |
|---|---|
| Student | Login, dashboard, profile changes, document upload/download, eligible courses, attendance summary, GPA, transcript, invoice and receipt access |
| Faculty | Assigned-course attendance management, grade entry before finalization, and denial for unassigned courses or locked grades |
| Administrator | Student registration, profile approval, course/catalog administration, grade override with reason, reports, exports, and audit review |
| Security controls | JWT HttpOnly cookies, CSRF protection, Argon2 password hashes, OTP expiry/reuse protection, lockout, encryption, tamper detection, ownership checks, and append-only audit records |
| Operational services | Health/readiness endpoints, migrations, static collection, Docker/Gunicorn/Nginx startup, deterministic document scanning, Mailpit, and mock payment callbacks |

The tested application packages are `accounts`, `students`, `academic`, `enrollments`, `attendance`, `grading`, `finance`, `portal`, `core`, and `config`. The requirement IDs used below are the implemented F-001 through F-018, NF-001 through NF-006, SR-001 through SR-005, and their associated TC identifiers.

## 4. Test objectives

- Verify functional requirements using repeatable automated tests.
- Verify authentication, authorization, password security, encryption, audit logging, and account protection.
- Verify student registration, profile approval, document validation, enrollment, attendance, grades, fees, payments, reports, and transcripts.
- Verify database migrations, Django configuration, service health, readiness, OpenAPI availability, and the login entry point.
- Measure statement/line and branch coverage.
- Identify checks requiring Playwright, MySQL, k6, production infrastructure, or manual review.

## 5. Scope

| Area | Features tested |
|---|---|
| Authentication | Login, identity, OTP password reset, account lockout, role access, alerts, and audit records |
| Student management | Generated student IDs, approval-based profile changes, secure document upload, malware-marker rejection, and ownership checks |
| Academic/enrollment | Current eligible offerings, prerequisites, duplicate/full-seat rules, deadline-aware dropping, and seat consistency |
| Attendance | Faculty assignment authorization, attendance percentage, threshold flagging, and summaries |
| Grading/transcripts | Grade finalization locks, faculty restrictions, administrator overrides, audit persistence, GPA/CGPA, PDF transcript, and verification |
| Finance | Fee formula, signed payment callbacks, mismatch handling, idempotency, and receipts |
| Reports/security | Report rows/exports, append-only audit behavior, ciphertext, tamper detection, access denial, and security alerts |
| Operations/UX | Django checks, migrations, health endpoints, OpenAPI, portal markup, and role-specific navigation |

## 6. Test levels and approach

1. **Unit/component tests:** focused Python/Django tests for password hashing, models, and business services.
2. **Integration/API tests:** Django `TestCase` and test client tests against real URLs, authentication, database transactions, uploads, exports, and seeded data.
3. **System/smoke tests:** Django checks, Python compilation, migration consistency, application startup, health endpoints, OpenAPI, and login page.
4. **Browser E2E/accessibility:** Playwright with system Chrome for login/navigation and an axe-core scan. Both browser tests were executed and passed.
5. **Infrastructure/performance:** MySQL, Docker, k6 evidence, deployment/TLS, backup/restore, and manual accessibility checks. MySQL/Docker and SQLite backup/restore were executed; k6 was unavailable for a new run and manual/production checks remain limited.

## 7. Test data and environment

- Deterministic `seed_demo` data is used for students, faculty, administrators, courses, offerings, attendance, grades, invoices, payments, and audit records.
- Local execution uses SQLite. The CI configuration separately targets MySQL 8.4.
- Playwright 1.65.1 and `/usr/bin/google-chrome` were installed for the final run; both browser test functions passed.
- The final full run recorded 74 passed tests, 0 failures, 0 errors, and 0 skips. The canonical SQLite suite recorded 39 passed tests and the canonical MySQL 8.4 suite recorded 39 passed tests.

## 8. Entry and exit criteria

### Entry criteria

- Source code, requirements, and `docs/TEST_MATRIX.md` are available.
- Dependencies and deterministic test data are available.
- Database migrations can be applied.
- Django system checks can run.

### Exit criteria

- No automated test failures or errors.
- Test results and skipped cases are recorded with command, date, and environment.
- Statement and branch coverage reports are generated.
- Health, readiness, OpenAPI, and login-page smoke checks pass.
- Browser, MySQL, load, production, and manual checks are either completed or explicitly recorded as pending.

### Suspension/resumption

Suspend testing for an environment outage, corrupted test data, or a blocking defect. After recovery, repeat the affected setup checks before resuming.

## 9. Risks and controls

| Risk | Control |
|---|---|
| SQLite differs from production MySQL | Run MySQL CI, concurrency, and trigger checks before production acceptance. |
| Browser dependencies are unavailable | Run Playwright/Chromium separately and report skipped cases as unexecuted. |
| Coverage does not prove correctness | Use requirement IDs, positive/negative cases, system checks, and manual review in addition to percentages. |
| Reports describe one checkout | Record date, revision, environment, commands, and working-tree state. |
| Untested paths remain | Use the coverage tables and HTML report to prioritize additional tests. |

## 10. Deliverables

| Required upload | Source file |
|---|---|
| STP Document | `STP_Document.md` |
| Unit testing Report | `Unit_Testing_Report.md` |
| System Testing Report | `System_Testing_Report.md` |
| Code Coverage Report | `Code_Coverage_Report.md` |
| Branch Coverage Report | `Branch_Coverage_Report.md` |

## 11. Traceability and executed evidence

The following entries reproduce the requirement/test mapping used for the test run. The test method names and observed outcomes are included here so the plan remains understandable without opening another document.

| Test ID | Test objective | Source | Observed result |
|---|---|---|---|
| TC-Auth-01/02/03 | Login/role access, five-failure lockout, audit/alert/notification, OTP expiry and reuse rejection | `tests/test_requirements.py` | PASS |
| TC-Reg-01/02/03 | Generated student ID, approval workflow, document validation, malware scan, and ownership | `tests/test_requirements.py` | PASS |
| TC-Enr-01/02/03/03a/03b | Eligibility, duplicate/full seats, before/after-deadline and repeated drop behavior | `tests/test_requirements.py` | PASS |
| TC-Att-01/02 | Faculty assignment, 48-hour rule, attendance percentage and threshold flag | `tests/test_requirements.py` | PASS |
| TC-Grd-01/01a-01g | Finalization, lock, override reason, rollback, authorization, and audit | `tests/test_requirements.py` | PASS |
| TC-Grd-02/03 | Known-dataset GPA and transcript PDF/verification | `tests/test_requirements.py` | PASS |
| TC-Fee-01/02 | Fee formula, signed callback, mismatch handling and idempotent receipt | `tests/test_requirements.py` | PASS |
| TC-Rpt-01/02 | Report rows/exports and append-only ciphertext audit behavior | `tests/test_requirements.py` | PASS |
| TC-Sec-01-06 | Password, TLS configuration, Argon2, denial audit, export alerts and tamper detection | `tests/test_requirements.py` | PASS |
| TC-Ops-01/02/03 | Health, readiness failure handling and SQLite backup/restore | `tests/test_requirements.py` and `test_requirements.py` | PASS |
| TC-Perf-01/02 | k6 profile configuration exists; historical load thresholds evaluated separately | `tests/test_requirements.py` | PASS for configuration; load thresholds FAILED |
| TC-UX-01/02 | Accessibility markup, browser axe scan, login/navigation and role-specific navigation | `tests/test_requirements.py` and `e2e/test_portal.py` | PASS |

## 12. References and links

The report above contains the project description, test approach, executed outcomes and limitations. The following links are supporting references, not substitutes for the information in this document:

- [Student Record System repository](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo)
- [Project overview and setup](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/README.md)
- [Architecture and module responsibilities](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/ARCHITECTURE.md)
- [Requirement/test traceability matrix](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/TEST_MATRIX.md)
- [Security controls](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/SECURITY.md)
- [Operations and backup procedures](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/OPERATIONS.md)
- [Raw test and coverage artifacts](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo/docs/reports)
