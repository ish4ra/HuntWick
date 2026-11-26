"""Check the installed Sherlock engine from outside the source tree."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run_request(executable, request, directory):
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(key, None)
    # The installed engine must run with its own interpreter and site data.
    env.update(PATH=directory, HTTP_PROXY="http://127.0.0.1:9",
               HTTPS_PROXY="http://127.0.0.1:9", NO_PROXY="")
    for key in ("http_proxy","https_proxy","all_proxy","no_proxy"):
        env.pop(key,None)
    process = subprocess.run(
        [str(executable)], input=json.dumps(request) + "\n", capture_output=True,
        encoding="utf-8", cwd=directory, env=env, timeout=60,
    )
    if process.returncode:
        raise RuntimeError(f"Engine exited with {process.returncode}: {process.stderr}")
    return [json.loads(line) for line in process.stdout.splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Engine executable or unpacked installer root")
    path = parser.parse_args().path.resolve()
    executable = path
    if path.is_dir():
        name = "huntwick-engine.exe" if os.name == "nt" else "huntwick-engine"
        candidates = [p for p in path.rglob(name) if p.is_file() and p.parent.name == "engine"]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one installed engine below {path}, found {candidates}")
        executable = candidates[0]

    with tempfile.TemporaryDirectory() as directory:
        catalog = run_request(executable, {"op": "catalog"}, directory)
        if [event["type"] for event in catalog] != ["catalog", "done"]:
            raise RuntimeError(f"Unexpected catalog event sequence: {[e.get('type') for e in catalog]}")
        sites = catalog[0]["sites"]
        if not any(site["name"] == "GitHub" for site in sites):
            raise RuntimeError("GitHub is missing from the bundled Sherlock catalog")
        # Sherlock rejects underscores on GitHub before making an HTTP request.
        events = run_request(executable, {
            "op": "search", "username": "with_underscore", "sites": ["GitHub"],
            "timeout": 2, "concurrency": 1,
        }, directory)
        if ([event["type"] for event in events] != ["result", "done"]
                or events[0]["platform"] != "GitHub" or events[0]["status"] != "inconclusive"):
            raise RuntimeError(f"Unexpected fixture result: {events}")
        # A closed local proxy exercises the packaged HTTP worker without reaching a site.
        failure = run_request(executable, {"op":"search","providerMode":"enhanced",
            "username":"fixture","sites":["Lichess"],"timeout":3,"concurrency":1},directory)
        if failure[0].get("provider") != "HuntWick public lookup" or failure[0].get("verdict") not in {"Connection failure","Timeout"}:
            raise RuntimeError("Packaged native public lookup did not report the offline connection failure.")
        maigret = run_request(executable, {"op":"search","providerMode":"maigret",
            "username":"with_underscore","sites":["GitHub"],"timeout":2,"concurrency":1}, directory)
        if [e['type'] for e in maigret] != ['result','done'] or (
                maigret[0].get('provider'), maigret[0].get('verdict')) != ('Maigret', 'Illegal'):
            raise RuntimeError("Bundled Maigret failed its offline username rule.")
        print(f"{executable} loaded {len(sites)} sites and completed the offline search fixture.")


if __name__ == "__main__":
    main()
