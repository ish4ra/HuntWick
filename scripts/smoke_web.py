"""Check a disposable local web image with its real engine and an offline handle."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

import httpx


def docker(*args, env=None):
    return subprocess.check_output(["docker", *args], text=True, env=env, stderr=subprocess.STDOUT).strip()


def expect_status(response, expected):
    if response.status_code != expected:
        raise RuntimeError(f"{response.request.method} {response.request.url.path} returned "
                           f"{response.status_code}, expected {expected}")


def wait_for_service(url):
    with httpx.Client(base_url=url, trust_env=False, timeout=3) as client:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                health = client.get("/healthz")
                if health.status_code == 200 and health.json() == {"status": "ok"}:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.5)
    raise RuntimeError("Container health check timed out.")


def check_service(url, password, username):
    with httpx.Client(base_url=url, trust_env=False, timeout=20) as client:
        for path in ["/", "/api/catalog"]:
            expect_status(client.get(path), 401)
        auth = ("huntwick", password)
        index = client.get("/", auth=auth)
        expect_status(index, 200)
        asset = re.search(r'<script\b[^>]*\bsrc="(/assets/[^"]+)"', index.text)
        if not asset:
            raise RuntimeError("Compiled frontend entry script was missing.")
        expect_status(client.get(asset[1]), 401)
        expect_status(client.get(asset[1], auth=auth), 200)
        catalog = client.get("/api/catalog", auth=auth)
        expect_status(catalog, 200)
        if "GitHub" not in {site["name"] for site in catalog.json()["sites"]}:
            raise RuntimeError("The hosted catalog lacks the offline GitHub fixture.")

        # A GitHub handle containing an underscore is rejected by the bundled
        # Sherlock rule before a network request, including on the first run.
        for index in range(6):
            payload = {"id": f"image-check-{index}", "username": username,
                       "sites": ["GitHub"], "timeout": 2, "concurrency": 1}
            response = client.post("/api/search", json=payload, auth=auth)
            expect_status(response, 200)
            events = [json.loads(line) for line in response.iter_lines()]
            if (len(events) != 2 or events[0].get("status") != "inconclusive"
                    or events[0].get("platform") != "GitHub"
                    or events[1] != {"id": payload["id"], "type": "done"}
                    or response.headers.get("cache-control") != "no-store"):
                raise RuntimeError("The offline engine stream or cache policy was unexpected.")
        expect_status(client.post("/api/search", json=payload, auth=auth), 429)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--browser", action="store_true", help="Use the authenticated Chromium search and export check")
    args = parser.parse_args()
    password = secrets.token_urlsafe(36)
    username = "image_fixture_" + secrets.token_hex(4)
    env = {**os.environ, "HUNTWICK_WEB_PASSWORD": password}
    container = docker("run", "--detach", "--publish", "127.0.0.1::8000",
                       "--read-only", "--tmpfs", "/tmp", "--memory", "512m",
                       "--env", "HUNTWICK_WEB_PASSWORD", args.image, env=env)
    try:
        address = docker("port", container, "8000/tcp")
        url = "http://" + address
        wait_for_service(url)
        if args.browser:
            script = Path(__file__).with_name("smoke_web_browser.py")
            subprocess.run([sys.executable, script, "--port", address.rsplit(":", 1)[1]],
                           env=env, check=True, timeout=90)
            subprocess.run([sys.executable, Path(__file__).with_name("test_web_radar.py"), "--port", address.rsplit(":", 1)[1]],
                           env=env, check=True, timeout=90)
        else:
            check_service(url, password, username)
        docker("stop", "--time", "5", container)
        logs = docker("logs", container)
        if any(value in logs for value in (password, username, "with_underscore", "image-check-", "/api/search")):
            raise RuntimeError("The container logged private request data.")
    finally:
        docker("rm", "--force", container)
    if not args.browser:
        print("Verified protected assets, catalog, real offline search and rate limiting.")
    print("Container logs passed the privacy check.")


if __name__ == "__main__":
    main()
