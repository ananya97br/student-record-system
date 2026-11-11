# CI test and coverage reports

The GitHub Actions workflow writes generated deliverables to this directory and
uploads the directory as the `test-and-coverage-reports` artifact. It contains:

- `unit-test-report.xml` — JUnit unit-test results.
- `coverage-report.txt` and `coverage.xml` — line-coverage reports.
- `branch-coverage-report.txt` and `coverage.json` — branch-aware coverage data.
- `coverage-html/` — browsable HTML coverage details.

The generated files are intentionally not committed because each run describes
a particular commit. Download the artifact from the workflow run and copy the
files here when preparing the Software Engineering mini-project deliverables.

The local validation results and checks not covered by that run are summarized
in [P-008 system validation evidence](../evidence/P-008.md).
