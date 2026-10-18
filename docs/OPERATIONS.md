# Operations runbook

## Configuration

Copy `.env.example` and use `python3 scripts/bootstrap.py` for local strong secrets/certificate generation. Production must explicitly set `DJANGO_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `LOOKUP_HMAC_KEY`, `JWT_SECRET_KEY`, payment/SMTP credentials, `DATABASE_URL`, hosts/origins, secure cookies, and document storage. Do not commit `.env`.

## Migrations and deployment

```bash
python manage.py makemigrations --check
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Docker runs migrations in the API entrypoint before Gunicorn. Use one migration runner when horizontally scaling; web replicas run with `RUN_MIGRATIONS=0`.

## Backups and restore

`scripts/backup.sh` copies SQLite in local mode or runs `mysqldump --single-transaction --routines --triggers` for MySQL. `scripts/restore.sh` restores either form. Back up the document volume/object storage and encryption-key metadata under the same retention policy. Test restoration to an isolated environment regularly.

## Retention and archival

`RETENTION_YEARS=10` and the `retention_years` SystemConfig document the policy. No automatic destructive cleanup task exists. Archive academic records, documents, and audit logs to encrypted durable storage after operational review; retrieve through an authorized administrative process. Synthetic dates should be used to test an eventual archive job rather than waiting ten years.

## Health and monitoring

- `/health/live` indicates process liveness.
- `/api/health/ready` executes a database readiness query.
- Track request latency/p95, error rate, DB health, authentication failures, payment/notification/report failures, export alerts, disk/document storage, and backup age.
- Use structured log aggregation and redact secrets before shipping logs.

## Scaling

Run multiple API/Web replicas behind Nginx or a managed load balancer, use MySQL connection pooling/read replicas where appropriate, a shared cache for rate limits, and shared object storage for documents. Use the k6 profiles as workload definitions; record actual environment and results rather than claiming targets by existence of the scripts.

## Provider replacement

Replace `core.notifications`, `core.scanner`, and `finance.services.MockPaymentGateway` behind their narrow adapters. Production payment callbacks must retain signature, reference, amount, and idempotency checks. SSO is intentionally disabled by default and must map verified identities to local roles before enabling.
