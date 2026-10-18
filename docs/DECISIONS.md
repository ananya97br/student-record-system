# Decisions and assumptions

1. **Requirement count mismatch:** the brief says 25 functional requirements, but the source enumerates and traces only `SRS-F-001` through `SRS-F-018`. All F-001–F-018 are implemented; no fictitious F-019–F-025 IDs were invented.
2. **Python/Django override:** the user explicitly requested Django/Python and no TypeScript. Django templates and vanilla JavaScript provide the browser client while retaining the required responsive/accessibility behavior.
3. **Student IDs:** generated as `STU-YYYY-####` using a locked yearly sequence.
4. **Grading:** the suggested data-driven 10-point scheme is seeded: A+ 90–100/10, A 80–89.99/9, B 70–79.99/8, C 60–69.99/7, D 50–59.99/6, E 40–49.99/5, F below 40/0. Admin can create schemes/bands.
5. **GPA:** credit-weighted grade points, displayed to two decimals; only locked/finalized course results count.
6. **Fees:** seeded in INR with base INR 100,000 and INR 5,000 per enrolled credit. The formula is data-driven `base + credits × per-credit - scholarship`.
7. **Scholarships:** the largest applicable percentage/fixed discount is applied once and capped at subtotal.
8. **Attendance:** `PRESENT` and `LATE` count; `ABSENT` and `EXCUSED` do not. Default threshold is 75% and is configurable.
9. **Grade workflow:** assigned faculty finalize/lock; admin/sysadmin overrides require a reason and are audited.
10. **Authentication:** signed HS256 JWT cookie with token-version revocation, SameSite=Lax, HttpOnly, Secure enabled in production. A database-backed session table was not selected because stateless horizontal scaling is useful here.
11. **Local payment:** HMAC-signed mock adapter with success/failure/cancel actions; no external credentials or card collection.
12. **Email:** Django SMTP adapter; console backend is a no-service local fallback and Mailpit is used by Docker.
13. **Malware:** deterministic development scanner detects the EICAR test string. The scanner interface is replaceable by ClamAV.
14. **SSO:** not enabled; local credential login is the baseline and an SSO provider can be added behind the authentication boundary.
15. **Encryption:** AES-256-GCM application fields plus HMAC lookup hashes for equality references. Development keys are generated into ignored `var/dev-secrets.json`; production must provide explicit secret-manager values.
16. **Database:** SQLite is used only for a clean local/test fallback. MySQL 8 is the Docker/production-like relational database.
