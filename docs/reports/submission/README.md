# Final submission files

The official PDF deliverables are in `docs/reports/`:

- `STP_Document.pdf`
- `Unit_Testing_Report.pdf`
- `System_Testing_Report.pdf`
- `Code_Coverage_Report.pdf`
- `Branch_Coverage_Report.pdf`

Markdown source copies are in this directory. Convert the PDFs only if you need to
make a local formatting change; the PDF files were rendered and checked after the
final test run.

Each report is intended to be self-contained. It explains the Student Record
System, the relevant workflow or measurement method, the actual executed result,
and the limitation/defect status before its final references section. GitHub links
are included only as supporting source and evidence links.

## Final measured results

- Full pytest discovery: **74 passed, 0 failed, 0 errors, 0 skipped**.
- Canonical Django suite: **39 passed** on SQLite.
- Canonical MySQL suite: **39 passed** on MySQL 8.4 in Docker.
- Browser/axe suite: **2 passed** with Playwright and system Chrome.
- Statement coverage: **74.15%** (`2011/2712`, 701 missed).
- Branch coverage: **41.47%** (`248/598`, 350 missing, 144 partial).
- Combined coverage.py line-plus-branch value: **68.25%**.

Existing historical k6 evidence for 2,000 and 10,000 virtual users is included in
the System Testing Report; both recorded runs failed their stated p95/failure-rate
thresholds. A new k6 run was not possible because `k6` is not installed.
