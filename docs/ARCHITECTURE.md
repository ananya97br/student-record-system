# Architecture

## Shape

This is a three-tier modular monolith:

```text
Browser (Django HTML + accessible vanilla JS)
             |
       Nginx public proxy
             |
  Django presentation/API layer
             |
  Domain modules and services
             |
      MySQL 8 / SQLite test fallback
       |       |        |
 documents  Mailpit  mock payment
```

The browser never connects to the database. JWT authentication is in an HttpOnly cookie and all authorization decisions occur server-side.

## Module boundaries

| Module | Responsibility |
|---|---|
| `accounts` | Custom identity model, lockout, OTP reset, notifications, security alerts, append-only audit records. |
| `academic` | Programs, semesters, courses, prerequisites, offerings, faculty, grading bands, fee structures, scholarships. |
| `students` | Student master records, encrypted profile fields, approval workflow, document storage/scanning/download. |
| `enrollments` | Eligibility, prerequisite checks, add/drop rules, atomic seat allocation/release. |
| `attendance` | Sessions, bulk attendance, assignment policy, 48-hour edit window, percentages and flags. |
| `grading` | Components, encrypted marks, finalization/locking, GPA/CGPA, transcripts and verification. |
| `finance` | Invoices, line items, payment adapter/callback, idempotency, receipts. |
| `portal` | Browser pages, dashboard summaries, report queries and exports. |
| `core` | Configuration, encryption, JWT, correlation IDs, error contract, audit/notification/scanner/report helpers. |

## Enrollment transaction

1. The student submits an offering ID.
2. The service starts a database transaction and locks the offering row.
3. It rechecks semester, program, prerequisites, duplicate state, deadline, status, and seats.
4. It creates/updates the enrollment and decrements `seats_available` in the same transaction.
5. Commit makes the seat and enrollment visible together.
6. Email notification runs from `on_commit`; failure is recorded and cannot undo enrollment.

The same pattern is used in reverse for drop/release. MySQL row locks provide the production concurrency guarantee; SQLite is a test/development fallback.

## Payment callback

```text
Student -> initiate payment -> pending Payment + mock checkout URL
Mock checkout -> HMAC callback -> signature check
                         -> reference/amount/currency check
                         -> locked idempotent transaction
                         -> invoice status + one Receipt
                         -> on-commit notification
```

Terminal callbacks are acknowledged without repeating state changes. No card data enters the application.

## Scaling

API/Web containers are stateless apart from shared MySQL and document storage. JWT token versioning provides revocation without an in-process session store. Nginx can fan out to multiple Django instances; use shared object storage for documents and a shared cache/rate-limit backend in production. Database indexes, pagination, bounded exports, connection reuse, and report row limits support the stated scale targets. The k6 profiles are executable evidence scripts, not claimed performance results.
