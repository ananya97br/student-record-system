# Test traceability matrix

The main automated suite is `tests/test_requirements.py`, run with `python manage.py test tests`. Method names use underscore-safe versions of the source test IDs; the exact IDs are retained in this matrix and the implementation log.

## Automated test-case traceability

The index below links the requirement/test IDs to the current test methods.
Update it whenever a sprint adds, removes, or changes a test case. A test ID in
the matrix is not evidence that a manual, browser, load, or infrastructure
check was executed; record those results separately with the test run and
environment.

| Test ID | Test method | Test source |
|---|---|---|
| TC-Auth-01 | `test_TC_Auth_01_successful_login_and_role_access` | `tests/test_requirements.py` |
| TC-UX-02 | `test_TC_UX_02_portal_navigation_is_role_specific` | `tests/test_requirements.py` |
| TC-Auth-02 | `test_TC_Auth_02_five_failures_lock_audit_notification_and_unlock` | `tests/test_requirements.py` |
| TC-Auth-03 | `test_TC_Auth_03_otp_reset_expiry_and_reuse` | `tests/test_requirements.py` |
| TC-Reg-01 | `test_TC_Reg_01_admin_creates_student_with_generated_id` | `tests/test_requirements.py` |
| TC-Reg-02 | `test_TC_Reg_02_profile_change_pending_until_approval` | `tests/test_requirements.py` |
| TC-Reg-03 | `test_TC_Reg_03_document_validation_scan_and_ownership` | `tests/test_requirements.py` |
| TC-Enr-01 | `test_TC_Enr_01_only_current_eligible_offerings` | `tests/test_requirements.py` |
| TC-Enr-02 | `test_TC_Enr_02_duplicate_and_full_seat_checks` | `tests/test_requirements.py` |
| TC-Enr-03 | `test_TC_Enr_03_drop_before_deadline_releases_seat` | `tests/test_requirements.py` |
| TC-Att-01 | `test_TC_Att_01_assigned_faculty_and_48_hour_rule` | `tests/test_requirements.py` |
| TC-Att-02 | `test_TC_Att_02_percentage_and_below_threshold_flag` | `tests/test_requirements.py` |
| TC-Grd-01 | `test_TC_Grd_01_grade_lock_and_admin_override_audit` | `tests/test_requirements.py` |
| TC-Grd-02 | `test_TC_Grd_02_known_dataset_gpa` | `tests/test_requirements.py` |
| TC-Grd-03 | `test_TC_Grd_03_transcript_pdf_and_verification` | `tests/test_requirements.py` |
| TC-Fee-01 | `test_TC_Fee_01_configured_formula` | `tests/test_requirements.py` |
| TC-Fee-02 | `test_TC_Fee_02_signed_callback_idempotent_receipt` | `tests/test_requirements.py` |
| TC-Rpt-01 | `test_TC_Rpt_01_report_rows_and_exports` | `tests/test_requirements.py` |
| TC-Rpt-02 | `test_TC_Rpt_02_audit_is_append_only_and_sensitive_values_ciphertext` | `tests/test_requirements.py` |
| TC-Sec-01 | `test_TC_Sec_01_password_plaintext_prohibition` | `tests/test_requirements.py` |
| TC-Sec-02 | `test_TC_Sec_02_tls_configuration_is_modern` | `tests/test_requirements.py` |
| TC-Sec-03 | `test_TC_Sec_03_argon2_hash_and_safe_auth_values` | `tests/test_requirements.py` |
| TC-Sec-04 | `test_TC_Sec_04_cross_role_denial_is_logged` | `tests/test_requirements.py` |
| TC-Sec-05 | `test_TC_Sec_05_repeated_exports_create_alert` | `tests/test_requirements.py` |
| TC-Sec-06 | `test_TC_Sec_06_encryption_tampering_fails` | `tests/test_requirements.py` |
| TC-Ops-01 | `test_TC_Ops_01_retention_and_health_evidence` | `tests/test_requirements.py` |
| TC-Perf-01 / TC-Perf-02 | `test_TC_Perf_01_and_TC_Perf_02_load_profiles_exist` | `tests/test_requirements.py` |
| TC-UX-01 | `test_TC_UX_01_accessible_portal_evidence` | `tests/test_requirements.py` |
| TC-UX-01 | `test_TC_UX_01_login_and_representative_pages` | `e2e/test_portal.py` |
| TC-UX-01 | `test_TC_UX_01_axe_login_page` | `e2e/test_portal.py` |

`TC-Perf-01` and `TC-Perf-02` currently verify that load profiles exist; they
do not execute or establish performance results. The two browser `TC-UX-01`
cases require the optional Playwright/browser environment described in
[`e2e/README.md`](../e2e/README.md). Consult the corresponding matrix rows for
manual and operational evidence that still requires separate execution.

## Post-sprint traceability update

After each sprint, compare changed requirements and acceptance criteria with
the automated test methods, update the exact test-ID links above and the
evidence column in the matrix, and identify any manual or environment-dependent
checks that remain unrun. Record actual test outcomes against the commit and
environment that produced them; do not infer execution from a test's presence.
The current P-005 documentation snapshot is in
[`docs/evidence/P-005.md`](evidence/P-005.md).

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
| NF-005 / TC-UX-01, TC-UX-02 | Portal accessibility markup assertions; student/faculty/admin navigation visibility and access restrictions | Keyboard, focus, screen-reader, and contrast review; browser axe review |
| NF-006 / TC-Perf-02 | k6 10,000-user executable profile | No unexecuted performance claim |
| SR-001 / TC-Sec-02 | Single Nginx public entry point on port 8000; production HTTPS termination remains an infrastructure concern | Browser/ proxy review |
| SR-002 / TC-Sec-03 | Argon2 settings and no plaintext test | Log review |
| SR-003 / TC-Sec-04 | Cross-role denial and audit | Ownership regression checks |
| SR-004 / TC-Sec-05 | Lock/export alert paths | Admin alert review |
| SR-005 / TC-Sec-06 | Authenticated ciphertext/tamper test | Key rotation runbook |

Regression coverage includes duplicate enrollment, full-seat behavior, duplicate payment callbacks, ownership checks, report authorization, transcript generation/verification, document ownership, and audited grade overrides.

P-008 local validation evidence and its environment limitations are recorded in
[P-008.md](evidence/P-008.md).

NF-005 test results and the remaining accessibility review items are recorded
in [NF-005.md](evidence/NF-005.md).
