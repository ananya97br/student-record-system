from __future__ import annotations

import os
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def launch_browser(manager):
    executable = os.getenv("CHROME_EXECUTABLE", "/usr/bin/google-chrome")
    options = {"headless": True}
    if Path(executable).exists():
        options["executable_path"] = executable
    try:
        return manager.chromium.launch(**options)
    except Exception as exc:
        pytest.skip(f"Chromium is not available in this environment: {exc}")


def test_TC_UX_01_login_and_representative_pages():
    with sync_playwright() as manager:
        browser = launch_browser(manager)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        assert page.get_by_role("heading", name="Sign in").is_visible()
        page.get_by_label("Login ID").fill("student1.demo")
        page.get_by_label("Password", exact=True).fill("Student1Demo!2026")
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/portal/dashboard")
        assert page.get_by_role("heading", name="Dashboard").is_visible()
        browser.close()


def test_TC_UX_01_axe_login_page():
    with sync_playwright() as manager:
        browser = launch_browser(manager)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        try:
            page.add_script_tag(url="https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js")
            result = page.evaluate("async () => await axe.run()")
        except Exception as exc:
            pytest.skip(f"axe-core could not be loaded in this environment: {exc}")
        assert result["violations"] == []
        browser.close()
