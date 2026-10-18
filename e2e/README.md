# Browser E2E and accessibility tests

These tests use Python Playwright and load axe-core in the browser. They are
optional because browser binaries are environment-sized dependencies.

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
BASE_URL=http://127.0.0.1:8000 .venv/bin/pytest e2e -q
```

The test skips cleanly when Playwright is not installed. In an environment
with browser/network access it checks login and representative portal pages.
