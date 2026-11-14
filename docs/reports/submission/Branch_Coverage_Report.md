# Branch Coverage Report

## What was measured

Branch coverage records measured decision outcomes, not just whether a line ran. It is useful for the Student Record System because authorization, enrollment capacity, withdrawal deadlines, payment signatures, health failures, and validation errors all have materially different outcomes.

## Command and scope

Branch tracing was enabled with the complete final pytest execution:

```text
BASE_URL=http://127.0.0.1:8000 .venv/bin/coverage run --branch --source=academic,accounts,attendance,config,core,enrollments,finance,grading,portal,students -m pytest --junitxml=docs/reports/unit-test-report.xml -q
```

## Actual branch statistics

- Total measurable branch arcs: **598**
- Covered branch arcs: **248**
- Missing branch arcs: **350**
- Partial branches: **144**
- **Branch coverage: 41.47%**
- Statement coverage in the same run: **74.15%**

## Package summary

| Package | Branches | Covered | Missing | Branch coverage |
|---|---:|---:|---:|---:|
| academic | 64 | 2 | 62 | 3.1% |
| accounts | 68 | 29 | 39 | 42.6% |
| attendance | 54 | 9 | 45 | 16.7% |
| config | 18 | 8 | 10 | 44.4% |
| core | 78 | 54 | 24 | 69.2% |
| enrollments | 42 | 25 | 17 | 59.5% |
| finance | 72 | 21 | 51 | 29.2% |
| grading | 78 | 37 | 41 | 47.4% |
| portal | 54 | 26 | 28 | 48.1% |
| students | 70 | 37 | 33 | 52.9% |
| **TOTAL** | **598** | **248** | **350** | **41.47%** |

## Decision-path interpretation

The suite exercises valid/invalid login, authorized/unauthorized access,
available/full/duplicate enrollment, before/after/repeated course drop, valid/
invalid payment callback, and ready/unavailable database branches. The remaining
missing arcs are concentrated in academic API error paths, attendance API paths,
finance API/service alternatives, and report-view alternatives.

Add focused tests for those branches, MySQL locking/trigger paths, and production configuration alternatives. The 41.47% branch result is reported separately from the 74.15% statement result because a line can execute without both outcomes of its decisions being exercised.

## References and links

The branch totals, package results, decision-path interpretation, and recommendations are included above. These links provide the source matrix and raw branch-aware evidence:

- [Student Record System repository](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo)
- [Coverage configuration](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/pyproject.toml)
- [Test traceability matrix](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/TEST_MATRIX.md)
- [Branch coverage text report](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/reports/branch-coverage-report.txt)
- [Coverage JSON with branch arcs](https://github.com/ananya97br/student-record-system/blob/docs/readme-demo/docs/reports/coverage.json)
- [HTML coverage details](https://github.com/ananya97br/student-record-system/tree/docs/readme-demo/docs/reports/coverage-html)
