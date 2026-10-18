# API reference

The live machine-readable contract is [`/api/openapi.json`](../api/openapi.json) when the server is running. A minimal local documentation page is [`/api/docs`](../api/docs).

## Authentication

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `POST /api/auth/unlock/<user-id>`
- `GET /api/auth/users`
- `PATCH /api/auth/users/<user-id>`
- `GET /api/auth/security-alerts`

Login returns a signed JWT in the `srs_access` HttpOnly cookie. Browser state-changing requests include `X-CSRFToken` matching the `csrftoken` cookie.

## Student and catalog

- `GET/PATCH /api/students/me`
- `GET /api/students/me/change-requests`
- `GET/POST /api/students/me/documents`
- `GET /api/students/documents/<id>/download`
- `GET/POST /api/students` (admin list/create)
- `GET /api/students/change-requests` and `POST /api/students/change-requests/<id>/decision`
- `GET/POST /api/catalog/programs`, `/semesters`, `/courses`, `/prerequisites`, `/offerings`
- `GET/POST /api/catalog/grading-schemes`, `/fee-structures`, `/scholarships`
- `GET/PUT /api/catalog/configuration`

## Enrollment, attendance, grades

- `GET /api/enrollments/eligible`, `GET/POST /api/enrollments`, `POST /api/enrollments/<id>/drop`
- `GET /api/attendance/faculty-offerings`, roster/session/bulk-record endpoints, student summary, flagged export
- Assessment components and marks under `/api/grades/components`
- `POST /api/grades/offerings/<id>/finalize`
- `GET /api/grades/results`, `/gpa`, `/transcript`, `/transcript/verify/<code>`
- `POST /api/grades/results/<id>/override`

## Fees and reports

- `GET /api/fees/invoices`, admin `POST /api/fees/invoices/generate`
- `POST /api/fees/payments/initiate`
- `POST /api/fees/payments/callback` with `X-Payment-Signature`
- `GET /api/fees/payments/<id>`, receipt PDF, reconciliation
- `GET /api/reports/enrollment|attendance|fees|grades` with filters, pagination, `format=pdf|xlsx`
- `GET /api/reports/audit/list` and dashboard summary

Every protected API performs server-side role and ownership checks. Errors use the documented `{code,message,correlationId,fieldErrors}` envelope and do not expose stack traces or filesystem paths.
