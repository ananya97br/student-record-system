# Code Coverage Report

## What was measured

Statement coverage records whether executable application statements ran during the test execution. The measured source scope includes authentication, student management, academic catalog, enrollment, attendance, grading, finance, portal, core security/utilities, and Django configuration. Test files, migrations, generated artifacts, and external services were not included in the denominator.

## Command and scope

```text
.venv/bin/coverage erase
BASE_URL=http://127.0.0.1:8000 .venv/bin/coverage run --branch --source=academic,accounts,attendance,config,core,enrollments,finance,grading,portal,students -m pytest --junitxml=docs/reports/unit-test-report.xml -q
.venv/bin/coverage report -m
.venv/bin/coverage html -d docs/reports/coverage-html
.venv/bin/coverage xml -o docs/reports/coverage.xml
.venv/bin/coverage json -o docs/reports/coverage.json --pretty-print
```

## Actual statistics

- Total executable statements: **2,712**
- Covered statements: **2,011**
- Missing statements: **701**
- **Statement/line coverage: 74.15%**
- Combined coverage.py line-plus-branch value: **68.25%**

The code percentage is the standalone statement/line figure. The 68.25% value
is shown separately because branch tracing combines line and branch data.

## Package summary

| Package | Statements | Covered | Missed | Line coverage |
|---|---:|---:|---:|---:|
| academic | 317 | 164 | 153 | 51.7% |
| accounts | 371 | 293 | 78 | 79.0% |
| attendance | 191 | 110 | 81 | 57.6% |
| config | 126 | 95 | 31 | 75.4% |
| core | 456 | 398 | 58 | 87.3% |
| enrollments | 165 | 137 | 28 | 83.0% |
| finance | 328 | 209 | 119 | 63.7% |
| grading | 326 | 263 | 63 | 80.7% |
| portal | 140 | 97 | 43 | 69.3% |
| students | 292 | 245 | 47 | 83.9% |
| **TOTAL** | **2,712** | **2,011** | **701** | **74.15%** |

Lowest statement coverage includes `academic/api_views.py` 22.9%,
`core/errors.py` 36.4%, `attendance/api_views.py` 41.7%,
`finance/web_views.py` 42.9%, and `finance/api_views.py` 47.7%.

These lower-coverage areas are primarily alternate API validation, error handling, report filters, and web-rendering paths. They are candidates for targeted additional tests; the percentage is not treated as proof that unexecuted code is correct.

## References and links

The numerical results and package table above are the report evidence. These links provide the reproducible commands, machine-readable outputs, and source configuration:

- [Student Record System repository](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo)
- [Coverage configuration](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/pyproject.toml)
- [Full test traceability](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/TEST_MATRIX.md)
- [Text coverage report](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/reports/coverage-report.txt)
- [Machine-readable coverage JSON](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/reports/coverage.json)
- [HTML coverage report](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo/docs/reports/coverage-html)
