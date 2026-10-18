# Test traceability matrix

The main automated suite is `tests/test_requirements.py`, run with `python manage.py test tests`. Method names use underscore-safe versions of the source test IDs; the exact IDs are retained in this matrix and the implementation log.

| Requirement/test ID | Automated evidence | Manual/operational evidence |
|---|---|---|
| F-001 / TC-Auth-01 | Login, `/me`, role denial | Role-aware portal navigation |
| F-002 / TC-Auth-02 | Five failures, lock, alert/audit, admin unlock | Mailpit lock email |
| F-003 / TC-Auth-03 | OTP success/reuse rejection | Expiry can be exercised with synthetic token date |
| F-004 / TC-Reg-01 | Admin create and generated ID | Student administration page |
| F-005 / TC-Reg-02 | Pending profile then approval | Admin approval UI |
| F-006 / TC-Reg-03 | Clean/infected/ownership document checks | Browser upload flow |
| F-007 / TC-Enr-01 | Current semester/eligibility response | Catalog UI |
| F-008 / TC-Enr-02 | Duplicate/full seat checks and transactional service | MySQL concurrency profile |
| F-009 / TC-Enr-03 | Drop releases seat | Deadline error path |
| F-010 / TC-Att-01 | Faculty assignment access | Bulk session UI/API |
| F-011 / TC-Att-02 | 50% seeded flag and summary | XLSX flagged export |
| F-012 / TC-Grd-01 | Locked result/admin override audit | Faculty gradebook flow |
| F-013 / TC-Grd-02 | Seeded 8.50 CGPA | Admin band configuration |
| F-014 / TC-Grd-03 | PDF and verification endpoint | Transcript visual review |
| F-015 / TC-Fee-01 | Configured invoice formula | Invoice UI |
| F-016 / TC-Fee-02 | Signed callback, mismatch, idempotent receipt | Mock checkout success/failure/cancel |
| F-017 / TC-Rpt-01 | JSON rows and PDF/XLSX response types | Filter/export UI |
| F-018 / TC-Rpt-02 | Append-only model and ciphertext test | MySQL immutable triggers |
| NF-001 / TC-Perf-01 | k6 2,000-user executable profile | Run only on suitable load infrastructure |
| NF-002 | Live/ready endpoints and Docker health | Monitoring/uptime procedure |
| NF-003 / TC-Sec-01 | Password/encryption tests | Security checklist |
| NF-004 / TC-Ops-01 | Configuration and backup/restore scripts | Synthetic retention review |
| NF-005 / TC-UX-01 | Semantic HTML/focus/contrast implementation | Browser axe/manual review |
| NF-006 / TC-Perf-02 | k6 10,000-user executable profile | No unexecuted performance claim |
| SR-001 / TC-Sec-02 | Single Nginx public entry point on port 8000; production HTTPS termination remains an infrastructure concern | Browser/ proxy review |
| SR-002 / TC-Sec-03 | Argon2 settings and no plaintext test | Log review |
| SR-003 / TC-Sec-04 | Cross-role denial and audit | Ownership regression checks |
| SR-004 / TC-Sec-05 | Lock/export alert paths | Admin alert review |
| SR-005 / TC-Sec-06 | Authenticated ciphertext/tamper test | Key rotation runbook |

Regression coverage includes duplicate enrollment, full-seat behavior, duplicate payment callbacks, ownership checks, report authorization, transcript generation/verification, document ownership, and audited grade overrides.
