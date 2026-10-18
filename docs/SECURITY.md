# Security notes

## Controls

- Passwords use Django's Argon2id hasher; plaintext passwords are never persisted or logged.
- OTPs are hashed with a server secret, expire after 10 minutes, are invalidated when a new OTP is issued, and are marked used in a transaction.
- JWTs are signed, HttpOnly, SameSite=Lax cookies. Logout/password reset increments `token_version` and invalidates old tokens.
- Login lockout occurs after five consecutive failures, creates an audit/security alert, and sends a notification. Login and reset endpoints are rate limited.
- Authorization is default-deny with role and ownership checks in every sensitive view. Denials create safe audit/security events.
- AES-256-GCM protects selected contact, mark/result, and payment-reference values. Payment reference HMACs support callback lookup without plaintext database indexing.
- Documents use extension allow-list, declared MIME validation, magic signatures, 5 MB limits, randomized paths, checksums, deterministic malware scan, and owner/admin download checks.
- Enrollment, grade finalization, invoice payment callbacks, and receipt creation use transactions and row locks/idempotency constraints.
- Helmet-equivalent Django/Nginx security headers include X-Frame-Options, content sniffing protection, and referrer policy. The bundled local stack uses one convenient HTTP entry point; production must terminate HTTPS with TLS 1.2/1.3 at the reverse proxy or load balancer.
- Correlation IDs are returned and included in safe operational logs. Secrets, passwords, OTPs, tokens, card data, encryption keys, and document bytes are not logged.
- Audit logs reject ORM updates/deletes and MySQL migrations add database triggers. No application service offers audit mutation.

## Threat boundaries

The local console email backend, deterministic scanner, SQLite fallback, and self-signed certificate are development conveniences. Production must use a managed secret store, real SMTP/provider adapters, ClamAV or equivalent, MySQL backups, HTTPS certificates trusted by clients, a shared cache/rate limiter, shared encrypted document storage, and monitoring.

## Key rotation

Field encryption and lookup HMAC keys are versioned operational concerns. Rotate by introducing a new key version, dual-reading during migration, re-encrypting records in bounded batches, then retiring the old key. Never change the only key without a planned re-encryption operation.

## Manual checks

Verify keyboard navigation, focus visibility, screen-reader labels, contrast, error summaries, upload rejection, ownership denial, and secure cookie flags in a browser. Automated functional tests cover the most important paths; browser axe checks should run in an environment with Playwright installed.
