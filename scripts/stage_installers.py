"""Collect installers built for one target and write a SHA-256 manifest."""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


FORMATS = {
    "x86_64-pc-windows-msvc": ("nsis/*.exe",),
    "aarch64-apple-darwin": ("dmg/*.dmg",),
    "x86_64-apple-darwin": ("dmg/*.dmg",),
    "x86_64-unknown-linux-gnu": ("deb/*.deb", "appimage/*.AppImage"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=FORMATS)
    parser.add_argument("--verify", action="store_true", help="Check the staged files against their manifest")
    args = parser.parse_args()
    target = args.target
    root = Path(__file__).resolve().parents[1]
    bundles = root / "src-tauri" / "target" / target / "release" / "bundle"
    output = root / "installers" / target
    version = json.loads((root / "package.json").read_text(encoding="utf-8"))["version"]
    manifest_path = output / f"SHA256SUMS-{target}.txt"
    manifest = []
    if not args.verify:
        output.mkdir(parents=True, exist_ok=True)
    for pattern in FORMATS[target]:
        installer = output / f"HuntWick-{version}-{target}{Path(pattern).suffix}"
        if not args.verify:
            matches = list(bundles.glob(pattern))
            if len(matches) != 1:
                raise RuntimeError(f"Expected one {pattern} under {bundles}, found {matches}.")
            shutil.copyfile(matches[0], installer)
        with installer.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        manifest.append(f"{digest}  {installer.name}\n")
    checksums = "".join(manifest)
    if args.verify:
        if checksums != manifest_path.read_text(encoding="ascii"):
            raise RuntimeError(f"Installer checksum mismatch in {manifest_path}")
        print(checksums, end="")
        if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(summary, "a", encoding="utf-8") as stream:
                stream.write(f"### Installer SHA-256 for {target}\n\n```text\n{checksums}```\n")
    else:
        manifest_path.write_text(checksums, encoding="ascii", newline="\n")


if __name__ == "__main__":
    main()
