"""Promote one owner-approved build using GitHub's Actions artifacts REST API."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import shutil
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

REPO = "ish4ra/HuntWick"
SHA = "7d203a5aa40d7338e3a2d3857a777f00ab4b91f8"
RUN = 45641860559
VERSION = "0.1.0-rc.4"
TAG = "v" + VERSION
API = f"https://api.github.com/repos/{REPO}"
PUBLIC = f"https://github.com/{REPO}/releases/download"
APP = Path("candidate").resolve()
OUT = APP / "installers"
# ID, original archive digest. Changing these pins requires a new owner review.
ARCHIVES = {
    "huntwick-aarch64-apple-darwin": (15036421995, "4086715e3fb9ee865ccef8d3606c143ffe8609228e10020cccf277ea35a252e2"),
    "huntwick-x86_64-apple-darwin": (15037577044, "6bbeefd63ced5be320be585845171dc346dfa58c8ced8f5612b686987566cb2f"),
    "huntwick-x86_64-pc-windows-msvc": (15035873083, "2088fa78581336a1a66949be80df8feb07f484cc2b0b1998b173e5b32d887480"),
    "huntwick-x86_64-unknown-linux-gnu": (15037460443, "fcdb9e9a49d9f6e6e639a3c6b5b6eb4da439fadb99174d39ed84de3776a75af0"),
    "promotion-files": (15038015297, "7d0188d058ad255b2f2afbf070baa61c09de2477cacf42cba699cdc7aecc9e04"),
}
KEY_HASH = "cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def api(path, method="GET", data=None, missing=False):
    request = Request(API + "/" + path, method=method,
                      headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                               "Content-Type": "application/json"},
                      data=json.dumps(data).encode() if data is not None else None)
    try:
        with urlopen(request, timeout=90) as response:
            return json.load(response)
    except HTTPError as error:
        if missing and error.code == 404:
            return None
        raise RuntimeError(f"GitHub {method} {path}: {error.code} {error.read().decode()}") from None


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url, dest, *, artifact=False, allow_missing=False):
    # curl strips Authorization on cross-host redirects. Never log redirect URLs.
    args = ["curl", "--silent", "--location", "--proto", "=https", "--proto-redir", "=https",
            "--max-time", "300", "--output", str(dest), "--write-out", "%{http_code}"]
    if artifact:
        args += ["--header", "Authorization: Bearer " + os.environ["GH_TOKEN"]]
    result = subprocess.run([*args, url], capture_output=True, text=True)
    if not result.returncode and allow_missing and result.stdout == "404":
        return False
    require(not result.returncode and result.stdout == "200",
            f"Download failed for {url}: curl {result.returncode}, HTTP {result.stdout}")
    return True


def verify_candidate(temp):
    run = api(f"actions/runs/{RUN}")
    require((run["head_sha"], run["conclusion"], run["head_branch"], run["path"],
             run["actor"]["login"], run["triggering_actor"]["login"], run["event"]) ==
            (SHA, "success", "build/production-candidate", ".github/workflows/ci.yml",
             "ish4ra", "ish4ra", "push"), "Unexpected production run")
    inventory = api(f"actions/runs/{RUN}/artifacts?per_page=100")
    require(inventory["total_count"] == len(ARCHIVES), "Unexpected artifact count")
    OUT.mkdir()
    offline = temp / "offline"
    offline.mkdir()
    for artifact in inventory["artifacts"]:
        name = artifact["name"]
        ident, expected = ARCHIVES[name]
        require((artifact["id"], artifact["digest"], artifact["expired"]) ==
                (ident, "sha256:" + expected, False), f"Unexpected artifact {name}")
        archive = temp / f"{ident}.zip"
        download(f"{API}/actions/artifacts/{ident}/zip", archive, artifact=True)
        require(digest(archive) == expected, f"Archive checksum mismatch: {name}")
        print(f"Verified {name}: {expected}", flush=True)
        with ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                require(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", entry.filename),
                        "Unexpected archive member")
                target = (offline if name == "promotion-files" else OUT) / entry.filename
                with target.open("xb") as output, bundle.open(entry) as source:
                    shutil.copyfileobj(source, output)
    require(hashlib.sha256(os.environ["HUNTWICK_ARTIFACT_PUBLIC_KEY"].strip().encode()).hexdigest()
            == KEY_HASH, "RC.3 public-key fingerprint mismatch")
    subprocess.run(["python", "scripts/prepare_candidate.py"], cwd=APP, check=True,
                   env={**os.environ, "GITHUB_RUN_ID": str(RUN), "GITHUB_SHA": SHA})
    require(json.loads((offline / "candidate.json").read_bytes()) ==
            {"version": VERSION, "commit": SHA, "run": str(RUN), "updaterKeySha256": KEY_HASH},
            "Incorrect offline candidate binding")
    for name in ["latest.json", "SHA256SUMS", "candidate.json"]:
        require((offline / name).read_bytes() == (OUT / name).read_bytes(),
                f"Offline {name} differs from independently verified output")
    manifest = json.loads((offline / "latest.json").read_bytes())
    require(set(manifest["platforms"]) ==
            {"windows-x86_64", "darwin-aarch64", "darwin-x86_64", "linux-x86_64"},
            "Incorrect target set")
    payloads = {line.split("  ")[1] for line in (OUT / "SHA256SUMS").read_text().splitlines()}
    require(len(payloads) == 7, "Expected five installers and two macOS updater archives")
    signatures = {entry["url"].rsplit("/", 1)[1] + ".sig" for entry in manifest["platforms"].values()}
    return sorted(payloads | signatures | {"SHA256SUMS", "latest.json"}), manifest


def release(tag, names):
    refpath = "git/ref/tags/" + tag
    ref = api(refpath, missing=True)
    if ref:
        require(ref["object"]["type"] == "commit" and ref["object"]["sha"] == SHA,
                f"Conflicting existing tag {tag}")
    current = api("releases/tags/" + tag, missing=True)
    if current is None:
        # Drafts may only be visible in the authenticated release inventory.
        page = 1
        while True:
            releases = api(f"releases?per_page=100&page={page}")
            matches = [r for r in releases if r["tag_name"] == tag]
            if matches:
                require(len(matches) == 1, f"Ambiguous release {tag}")
                current = matches[0]
                break
            if len(releases) < 100:
                break
            page += 1
    if current is None:
        current = api("releases", "POST", {"tag_name": tag, "target_commitish": SHA,
                      "name": tag, "draft": True, "prerelease": True, "make_latest": "false"})
    rid = current["id"]
    print(f"{tag} release ID {rid}", flush=True)
    require(current["prerelease"] and (ref or current["target_commitish"] == SHA),
            f"Unexpected release state for {tag}")
    existing = {a["name"]: a for a in current["assets"]}
    require(set(existing) <= set(names), f"Unexpected assets on {tag}")
    for name in names:
        if name in existing:
            require(existing[name]["state"] == "uploaded" and
                    existing[name]["digest"] == "sha256:" + digest(OUT / name),
                    f"Conflicting asset {name} on release {rid}")
        else:
            require(current["draft"], f"Missing asset on published release {rid}: {name}")
            subprocess.run(["gh", "release", "upload", tag, str(OUT / name), "--repo", REPO], check=True)
    staged = api(f"releases/{rid}")
    require({a["name"]: a["digest"] for a in staged["assets"] if a["state"] == "uploaded"} ==
            {name: "sha256:" + digest(OUT / name) for name in names}, "Staged asset mismatch")
    if current["draft"]:
        if not ref:
            api("git/refs", "POST", {"ref": "refs/tags/" + tag, "sha": SHA})
        require(api(refpath)["object"]["sha"] == SHA, f"Tag changed: {tag}")
        api(f"releases/{rid}", "PATCH", {"draft": False, "prerelease": True, "make_latest": "false"})
    require(api(refpath)["object"]["sha"] == SHA, f"Incorrect published tag {tag}")


def verify_public(temp, tag, names):
    for name in names:
        download(f"{PUBLIC}/{tag}/{name}", temp / name)
        require(digest(temp / name) == digest(OUT / name), f"Public asset mismatch for {name}")


def promote(temp):
    names, manifest = verify_candidate(temp)
    release(TAG, names)
    verify_public(temp, TAG, names)
    for entry in manifest["platforms"].values():
        name = entry["url"].rsplit("/", 1)[1]
        require(entry["url"] == f"{PUBLIC}/{TAG}/{name}", "Unexpected manifest URL")
        subprocess.run(["node", "scripts/verify-update.mjs", temp / name, VERSION], cwd=APP, check=True)
    release("updates-preview", ["latest.json"])
    verify_public(temp, "updates-preview", ["latest.json"])
    stable = temp / "stable.json"
    if download(f"{PUBLIC}/updates-stable/latest.json", stable, allow_missing=True):
        require(json.loads(stable.read_bytes())["version"] != VERSION, "Stable advertises RC.4")
    print("Verified public versioned assets, preview manifest and stable isolation.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        promote(Path(directory))
