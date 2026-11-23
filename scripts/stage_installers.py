"""Collect installers built for one target and write a SHA-256 manifest."""

import argparse
import hashlib
import json
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
    target = parser.parse_args().target
    root = Path(__file__).resolve().parents[1]
    bundles = root / "src-tauri" / "target" / target / "release" / "bundle"
    output = root / "installers" / target
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((root / "package.json").read_text(encoding="utf-8"))["version"]
    manifest = []
    for pattern in FORMATS[target]:
        matches = list(bundles.glob(pattern))
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {pattern} under {bundles}, found {matches}.")
        installer = output / f"HuntWick-{version}-{target}{matches[0].suffix}"
        shutil.copyfile(matches[0], installer)
        with installer.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        manifest.append(f"{digest}  {installer.name}\n")
    (output / f"SHA256SUMS-{target}.txt").write_text(
        "".join(manifest), encoding="ascii", newline="\n"
    )


if __name__ == "__main__":
    main()
