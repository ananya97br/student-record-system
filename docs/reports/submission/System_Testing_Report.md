# System Testing Report

## System under test

The assembled system consists of Django portal pages and REST APIs behind Nginx, with Gunicorn serving the application, MySQL 8.4 in the container path, Mailpit for local mail, deterministic document scanning, and a mock payment provider. The validation used synthetic demo data only and did not expose passwords or personal student information.

## Executed validation

| Check | Result |
|---|---|
| Django check, compilation, migrations, static collection | PASS |
| Docker build/start with MySQL 8.4, Gunicorn, Nginx, Mailpit | PASS after entrypoint mode fix |
| `/health/live`, `/api/health/ready`, `/api/openapi.json` | PASS; HTTP 200 |
| Login page and live authenticated workflow reads | PASS; login, `/me`, eligible enrollment, attendance, GPA, transcript, dashboard all HTTP 200 |
| Browser login/navigation and axe scan | PASS; 2/2 |
| Canonical MySQL test suite | PASS; 39/39 |

## System scenarios

| Scenario | Evidence | Status |
|---|---|---|
| Student login and dashboard | Live API plus Playwright | PASS |
| Administrator registration | TC-Reg-01, SQLite and MySQL | PASS |
| Profile approval | TC-Reg-02 | PASS |
| Enrollment and withdrawal | TC-Enr-01 to TC-Enr-03b | PASS |
| Attendance | TC-Att-01/02 | PASS |
| Grade, GPA/CGPA, transcript | TC-Grd-01 to TC-Grd-03 | PASS |
| Invoice/payment | TC-Fee-01/02 | PASS |
| Reports, authorization, security | TC-Rpt and TC-Sec | PASS |

## Performance evidence

Existing repository evidence was inspected and preserved:

- NF-001, 2,000 VUs: 130,987 requests, p95 **3.95 s**, HTTP failure **46.67%**; thresholds failed.
- NF-006, 10,000 VUs: 306,327 requests, p95 **22.14 s**, HTTP failure **60.12%**; thresholds failed.

A new k6 run was not executed because `k6` is not installed. These results are
not presented as passing performance evidence.

The available evidence therefore does not establish a supported maximum user count. At 2,000 virtual users the tested setup failed 46.67% of HTTP requests, and at 10,000 virtual users it failed 60.12%. Capacity requires tuning and a repeatable load test on production-like infrastructure.

## Defects and limitations

- `infra/scripts/docker-entrypoint.sh` was mode 0644 even though Docker executes it directly. The executable bit was corrected to 0755; the Docker stack then passed.
- A combined MySQL run of duplicated canonical and supplemental test classes exposed one test-data/sequence isolation failure. The isolated canonical MySQL suite passed 39/39.
- `check --deploy` emits five expected warnings under local development settings; production HTTPS, HSTS, secure cookies, and DEBUG configuration require review.
- Manual accessibility, production TLS/proxy, centralized monitoring, and backup retention review remain separate operational tasks.

Live evidence: `docs/reports/raw/docker-system-live.txt`.

## References and links

The results and limitations are stated above; these links are supporting evidence and implementation references:

- [Student Record System repository](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo)
- [API contract and endpoints](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/API.md)
- [Architecture](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/ARCHITECTURE.md)
- [Operations runbook](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/OPERATIONS.md)
- [2,000-user load evidence](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/evidence/NF-001.md)
- [10,000-user load evidence](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/evidence/NF-006.md)
- [System-test raw logs](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo/docs/reports/raw)
