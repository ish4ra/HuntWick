"""Stream an Actions artifact back from GitHub and check its upload digest."""
import hashlib
import os
import re
import subprocess
import time


def verify():
    repository = os.environ["GITHUB_REPOSITORY"]
    artifact_id = os.environ["ARTIFACT_ID"]
    expected = os.environ["ARCHIVE_SHA256"].removeprefix("sha256:").lower()
    if not artifact_id.isdecimal() or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Missing upload ID or SHA256 digest")
    endpoint = f"repos/{repository}/actions/artifacts/{artifact_id}/zip"
    # The artifact can take a few seconds to become visible through the REST
    # endpoint. Stream the ZIP so large AppImages do not need a second disk copy.
    for delay in (0, 5, 15, 30):
        time.sleep(delay)
        with subprocess.Popen(["gh", "api", endpoint], stdout=subprocess.PIPE) as fetch:
            digest = hashlib.file_digest(fetch.stdout, "sha256").hexdigest()
            code = fetch.wait()
        if code == 0 and digest == expected:
            print(f"Verified downloaded archive {artifact_id}, SHA256 {digest}", flush=True)
            return
        reason = f"GitHub CLI exit {code}" if code else f"received {digest}, expected {expected}"
        print(f"Archive {artifact_id}: {reason}", flush=True)
    raise RuntimeError(f"Could not verify artifact {artifact_id} after four downloads ({reason})")


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"::error title=Archive verification::{error}", flush=True)
        raise
