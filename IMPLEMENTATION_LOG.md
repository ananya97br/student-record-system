# Implementation Log

## Current status

The original repository was an empty Python scaffold. The complete implementation is a Django/Python modular monolith; the earlier TypeScript/Node direction is intentionally not used.

## Completed phases

| Phase | Status | Notes |
|---|---|---|
| 1. Inspect and scaffold | Complete | Django project, settings, environment contract, templates/static client, shared utilities, and docs skeleton. |
| 2. Infrastructure and database | Complete | MySQL Docker path, SQLite fallback, normalized models, migrations, MySQL audit triggers, single-port Nginx proxy, Mailpit, bootstrap. |
| 3. Authentication/RBAC/security base | Complete | Argon2id, JWT cookies, lockout, OTP reset, CSRF, rate limiting, correlation IDs, alerts, audit. |
| 4. Academic/admin master data | Complete | Programs, semesters, courses, prerequisites, offerings, faculty, grading/fee configuration APIs and admin UI. |
| 5. Student records/documents | Complete | Generated IDs, encrypted profile fields, approval workflow, secure PDF/JPEG upload/scanning/download. |
| 6. Enrollment | Complete | Eligibility, prerequisites, deadlines, duplicate prevention, atomic seats, drop/release, notification isolation. |
| 7. Attendance | Complete | Assigned faculty sessions, bulk records, 48-hour rule, percentages, threshold flags, XLSX export. |
| 8. Grades/GPA/transcript | Complete | Components, encrypted marks, weighted bands, locking/override, SGPA/CGPA, PDF/verification. |
| 9. Fees/payments | Complete | Versioned fee formula, scholarships, invoices, HMAC mock gateway, idempotency, receipts, sandbox UI. |
| 10. Reports/audit/alerts | Complete | Four filtered reports, pagination, PDF/XLSX, export detection, audit review/security alerts. |
| 11. Accessibility/operations/performance | Complete | Semantic accessible UI with sufficient default contrast, health, backup/restore, retention notes, k6 profiles, E2E/axe harness. |
| 12. Full verification | Complete with documented environment limits | Local tests, SQLite smoke, Docker/MySQL single-entrypoint smoke, and browser E2E passed; full target k6 was not executed here. |

## Confirmed decisions

- Student IDs use `STU-YYYY-####`.
- The seeded grading scheme is the specified configurable 10-point A+–F scheme.
- Demo fees use INR 100,000 base plus INR 5,000 per enrolled credit.
- `PRESENT` and `LATE` count as attended; `ABSENT` and `EXCUSED` do not.
- Faculty can finalize grades; admin/sysadmin overrides require a reason and audit entry.
- Authentication uses a signed JWT in an HttpOnly cookie with token-version invalidation.
- The largest eligible scholarship is applied once, capped at the invoice subtotal.

## Assumptions to record

- SQLite is a dependency-free development/test fallback; Docker uses MySQL 8.
- Django templates and accessible vanilla JavaScript replace the brief's React/TypeScript client because the user explicitly requested Django/Python and no TypeScript.

## Validation

Validated commands and results:

- `uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt` — passed.
- `python manage.py check` — passed with no issues.
- `python manage.py makemigrations --check --dry-run` — passed; no model changes pending.
- `python manage.py migrate` — passed on clean SQLite and Docker MySQL.
- `python manage.py seed_demo` — passed and is idempotent for demo data.
- `python manage.py test tests -v 1` — **27 passed**.
- `pytest -q` — **29 passed** after installing the optional Playwright package and using the available system Chrome.
- `BASE_URL=http://127.0.0.1:8000 pytest e2e -q` — **2 passed**, including axe-core login-page accessibility checks.
- `node --check static/js/app.js` — passed (used only as a JavaScript syntax checker; the application runtime is Python/Django).
- `scripts/bootstrap.py` and `docker compose config --quiet` — passed.
- `scripts/smoke.sh` against local Django — passed.
- `scripts/bootstrap.py` after `cp .env.example .env` — repaired placeholder secrets without rotating the existing development encryption key; local `seed_demo` then passed.
- Optional Playwright/axe browser checks using installed system Chrome — **2 passed**; fixed the password-label selector and brand-badge contrast issue.
- `scripts/smoke.sh` through the single Docker application URL — passed.
- Docker single public URL `http://localhost:8000` — portal/API/report/payment routes verified; no public 8443/8080 application ports remain.
- Docker static CSS/JavaScript delivery through WhiteNoise — passed with HTTP 200 responses.
- SQLite backup/restore and MySQL `mysqldump --no-tablespaces` backup — passed.
- Docker build/start — passed after enabling MySQL trigger creation with `--log-bin-trust-function-creators=1`.
- Docker single-entrypoint `/api/health/ready`, `/api/openapi.json`, login, and portal rendering — passed.
- MySQL direct `UPDATE accounts_auditlog ...` — rejected by the `srs_audit_no_update` trigger with `Audit log is append-only`.
- k6 2,000/10,000-user target runs — not executed because this environment is not a suitable full-scale load generator; executable profiles remain in `load/k6/`.

## Known limitations

- Full 2,000- and 10,000-concurrent-user performance claims are intentionally not made; `k6` is not installed in this environment, so only the executable profiles and application-level checks exist.
- The default malware adapter is the deterministic EICAR-compatible development scanner. `ClamAVScanner` is replaceable/optional and was not run in this environment.
- Production deployments must replace generated/local secrets, self-signed TLS, Mailpit/console email, mock payments, SQLite fallback, and local document storage with managed services.
