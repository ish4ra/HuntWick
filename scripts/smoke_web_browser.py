"""Exercise the local private web build with Playwright and an offline Sherlock check."""

import argparse
import csv
import os
import shutil
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which("chromium"))
        page = browser.new_page(http_credentials={
            "username": "huntwick", "password": os.environ["HUNTWICK_WEB_PASSWORD"],
        })
        page.goto(f"http://127.0.0.1:{args.port}/")
        github = page.get_by_role("checkbox", name="GitHub", exact=True)
        expect(github).to_be_visible()
        for checkbox in page.locator(".web-platforms input").all():
            checkbox.uncheck()
        github.check()
        page.locator("#username").fill("with_underscore")
        page.locator('button[type="submit"]').click()
        page.get_by_role("button", name="All results").click()
        expect(page.get_by_role("cell", name="Inconclusive", exact=True)).to_be_visible()
        page.get_by_role("button", name="Export", exact=True).click()
        with page.expect_download() as result:
            page.get_by_role("button", name="Export CSV").click()
        with Path(result.value.path()).open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 1 and rows[0]["Username"] == "with_underscore"
        assert rows[0]["Platform"] == "GitHub" and rows[0]["Status"] == "inconclusive"
        assert rows[0]["Search started (UTC)"].endswith("Z")
        print("Real web search rendered one inconclusive GitHub result and downloaded matching CSV.")
        browser.close()


if __name__ == "__main__":
    main()
