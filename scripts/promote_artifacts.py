"""Promote one owner-approved build using GitHub's Actions artifacts REST API."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import shutil
import subprocess
import argparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

REPO = "ish4ra/HuntWick"
SHA = "4c283babbd4e6a4874e8633701bfeade2690f718"
RUN = 46053737732
VERSION = "0.1.0-rc.6"
TAG = "v" + VERSION
API = f"https://api.github.com/repos/{REPO}"
PUBLIC = f"https://github.com/{REPO}/releases/download"
APP = Path("candidate").resolve()
OUT = APP / "installers"
# ID, original archive digest. Changing these pins requires a new owner review.
ARCHIVES = {'huntwick-aarch64-apple-darwin': (15225818008, '4da1a8902b08d1b003f3158fc29e56ca2ab1db406cd92f9653ae8f75a1f5da37'),
 'huntwick-x86_64-apple-darwin': (15226569453, '19259e1941895a8f68026177d9ffb69600c31397832d27be4632c7d6b3ea10ba'),
 'huntwick-x86_64-pc-windows-msvc': (15225444679, '4e4cfd552102a6b1c55731726c02d9ac228175ae58fa7dfb31aa03707c57da1d'),
 'huntwick-x86_64-unknown-linux-gnu': (15225299553, 'a7679a0fda5a65d13806375b7ba6e7e546a8e66ba2c4c2b701cbec2a750c23d8'),
 'promotion-files': (15226294384, 'e992705bec75cf0d9c110ce2d04a887458a12aedf388e81e8d90b62e9338708a')}
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
    require(re.fullmatch(r"[0-9a-f]{40}", SHA) and RUN > 0 and len(ARCHIVES) == 5, "Production pins missing")
    run = api(f"actions/runs/{RUN}")
    require((run["head_sha"], run["conclusion"], run["head_branch"], run["path"],
             run["actor"]["login"], run["triggering_actor"]["login"], run["event"]) ==
            (SHA, "success", "build/production-candidate", ".github/workflows/ci.yml",
             "ish4ra", "ish4ra", "push"), "Unexpected production run")
    inventory = api(f"actions/runs/{RUN}/artifacts?per_page=100")
    require(inventory["total_count"] == len(ARCHIVES), "Unexpected artifact count")
    require({a["name"] for a in inventory["artifacts"]} == set(ARCHIVES), "Unexpected artifact names")
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
            == KEY_HASH, "Installed updater public-key fingerprint mismatch")
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
    suffixes = {
        "aarch64-apple-darwin": (".dmg", ".app.tar.gz"),
        "x86_64-apple-darwin": (".dmg", ".app.tar.gz"),
        "x86_64-pc-windows-msvc": (".exe",),
        "x86_64-unknown-linux-gnu": (".deb", ".AppImage"),
    }
    expected_payloads = {f"HuntWick-{VERSION}-{target}{suffix}"
                         for target, extensions in suffixes.items() for suffix in extensions}
    require(payloads == expected_payloads, "Unexpected installer and updater inventory")
    require({f.name for f in offline.iterdir()} == {"latest.json", "SHA256SUMS", "candidate.json"},
            "Unexpected offline promotion inventory")
    require(manifest["version"] == VERSION, "Unexpected manifest version")
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
                      "name": tag, "body": json.loads((OUT / "latest.json").read_bytes())["notes"],
                      "draft": True, "prerelease": True, "make_latest": "false"})
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


PREVIEW = "updates-preview"
RC4 = ("latest-0.1.0-rc.4.json", 794590979, "98cdaa90f1fdef0ade2ff84d9d3489453f69022238b5597bbd1a33efaa3c37a4")
RC5 = ("latest-0.1.0-rc.5.json", 795831425, "26a150727f70e68ec5d6510e4f68a4e2362f43d103e7ef1bd1e5f8d33c26577a")


def preview_inventory():
    feed = api("releases/tags/" + PREVIEW)
    require(feed["id"] == 459033318 and feed["prerelease"] and not feed["draft"],
            "Unexpected preview release")
    return {a["name"]: a for a in feed["assets"]}


def matches(asset, pin):
    return (asset is not None and asset["id"] == pin[1] and asset["state"] == "uploaded"
            and asset["digest"] == "sha256:" + pin[2])


def check_preview(assets, new):
    staging = "latest-" + VERSION + ".json"
    require(set(assets) <= {RC4[0], RC5[0], staging, "latest.json"}, "Unexpected preview inventory")
    require(matches(assets.get(RC4[0]), RC4), "RC.4 rollback changed")
    live = assets.get("latest.json")
    backup = assets.get(RC5[0])
    staged = assets.get(staging)
    if staged:
        require(staged["digest"] == new and staged["state"] == "uploaded", "Unexpected staged manifest")
    if matches(live, RC5) and not backup:
        return "previous"
    require(matches(backup, RC5), "RC.5 rollback changed")
    if not live and staged:
        return "paused"
    require(live and live["digest"] == new and live["state"] == "uploaded" and not staged,
            "Unexpected active preview")
    return "active"


def verify_rollbacks(temp, assets):
    for pin in (RC4, RC5):
        name = pin[0] if matches(assets.get(pin[0]), pin) else "latest.json"
        require(matches(assets.get(name), pin), "Missing pinned rollback")
        path = temp / pin[0]
        download(f"{PUBLIC}/{PREVIEW}/{name}", path)
        require(digest(path) == pin[2], "Public rollback manifest mismatch")


def preview_preflight(temp):
    new = "sha256:" + digest(OUT / "latest.json")
    assets = preview_inventory()
    state = check_preview(assets, new)
    verify_rollbacks(temp, assets)
    return state


def update_preview(temp):
    """Activate versioned bytes last and retain both pinned rollback assets."""
    new = "sha256:" + digest(OUT / "latest.json")
    staging = "latest-" + VERSION + ".json"
    assets = preview_inventory()
    state = check_preview(assets, new)
    if state == "active":
        return
    if staging not in assets:
        path = temp / staging
        shutil.copyfile(OUT / "latest.json", path)
        subprocess.run(["gh", "release", "upload", PREVIEW, str(path), "--repo", REPO], check=True)
    assets = preview_inventory()
    state = check_preview(assets, new)
    staged = assets[staging]
    def rename(asset, name):
        api(f"releases/assets/{asset['id']}", "PATCH", {"name": name})
    if state == "previous":
        rename(assets["latest.json"], RC5[0])
    try:
        rename(staged, "latest.json")
    except Exception:
        current = preview_inventory()
        if (matches(current.get(RC4[0]), RC4) and matches(current.get(RC5[0]), RC5)
                and "latest.json" not in current):
            rename(current[RC5[0]], "latest.json")
        raise
    require(preview_preflight(temp) == "active", "Activation or rollback verification failed")


def promote(temp):
    names, manifest = verify_candidate(temp)
    preview_preflight(temp)
    release(TAG, names)
    verify_public(temp, TAG, names)
    for entry in manifest["platforms"].values():
        name = entry["url"].rsplit("/", 1)[1]
        require(entry["url"] == f"{PUBLIC}/{TAG}/{name}", "Unexpected manifest URL")
        subprocess.run(["node", "scripts/verify-update.mjs", temp / name, VERSION], cwd=APP, check=True)
    update_preview(temp)
    verify_public(temp, "updates-preview", ["latest.json"])
    stable = temp / "stable.json"
    if download(f"{PUBLIC}/updates-stable/latest.json", stable, allow_missing=True):
        require(json.loads(stable.read_bytes())["version"] != VERSION, "Stable advertises candidate")
    print("Verified public versioned assets, preview manifest and stable isolation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        if args.verify_only:
            names, manifest = verify_candidate(Path(directory))
            require(preview_preflight(Path(directory)) == "previous", "Rehearsal requires the pinned RC.5 preview")
            print(f"::notice title=Verified preview manifest SHA-256::{digest(OUT / 'latest.json')}")
            for platform, entry in manifest["platforms"].items():
                print(f"::notice title=Verified {platform} updater signature::{entry['signature']}")
            for name in names:
                if name.endswith((".dmg", ".AppImage", ".deb", ".exe")):
                    print(f"::notice title=Verified installer::{name} {(OUT/name).stat().st_size} bytes")
        else:
            promote(Path(directory))
