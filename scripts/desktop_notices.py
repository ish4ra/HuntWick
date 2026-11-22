"""Ship local dependency notices alongside the installer resources."""
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine/dist/huntwick-engine"
DEST = ENGINE / "notices/desktop"


def run(args, directory=ROOT):
    return subprocess.check_output(args, cwd=directory, text=True, encoding="utf-8")


def collect(group, name, version, license_id, directory, license_file=None):
    target = DEST / group / (name.replace("/", "_") + "-" + version)
    target.mkdir(parents=True, exist_ok=True)
    candidates = {item for item in directory.iterdir()
                  if item.name.lower().startswith(("copying", "licence", "license", "notice", "copyright"))}
    if license_file:
        candidates.add(directory / license_file)
    for file in sorted(candidates):
        if file.is_file():
            shutil.copyfile(file, target / file.name)
        elif file.is_dir():
            shutil.copytree(file, target / file.name, dirs_exist_ok=True)
    return {"name": name, "version": version, "license": license_id}


def main():
    if not ENGINE.is_dir():
        raise SystemExit("Package the engine first.")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"
    index = []
    for path in run([npm, "ls", "--omit=dev", "--all", "--parseable"]).splitlines():
        directory = Path(path)
        if directory == ROOT:
            continue
        package = json.loads((directory / "package.json").read_text(encoding="utf8"))
        index.append(collect("npm", package["name"], package["version"], package.get("license"), directory))
    host = next(line.split()[1] for line in run(["rustc", "-vV"]).splitlines() if line.startswith("host:"))
    metadata = json.loads(run(["cargo", "metadata", "--locked", "--format-version", "1",
                               "--filter-platform", host], ROOT / "src-tauri"))
    used = {node["id"] for node in metadata["resolve"]["nodes"]}
    for package in metadata["packages"]:
        if package["source"] and package["id"] in used:
            index.append(collect("cargo", package["name"], package["version"], package.get("license"),
                                 Path(package["manifest_path"]).parent, package.get("license_file")))
    (DEST / "dependencies.json").write_text(json.dumps(index, indent=2), encoding="utf8")
    shutil.copyfile(ROOT / "LICENSE", DEST / "HuntWick-LICENSE.txt")
    shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", DEST / "THIRD_PARTY_NOTICES.md")
    print(f"Collected metadata and available license files for {len(index)} desktop packages.")


if __name__ == "__main__":
    main()
