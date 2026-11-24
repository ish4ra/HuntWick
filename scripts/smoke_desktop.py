"""Launch an installed HuntWick desktop and wait for its native/webview check."""

import argparse
import ntpath
import os
import subprocess
import tempfile
from pathlib import Path


def desktop_environment(source, windows):
    env = {key.upper(): value for key, value in source.items()} if windows else dict(source)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    if windows:
        root = env["SYSTEMROOT"]
        env["PATH"] = ntpath.join(root, "System32") + ";" + root
    else:
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    executable = parser.parse_args().executable.resolve(strict=True)
    env = desktop_environment(os.environ, os.name == "nt")
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            [str(executable), "--verify-install"], env=env, cwd=directory,
            timeout=90, check=True,
        )
    print(f"{executable} verified the installed catalog and rendered search form.")


if __name__ == "__main__":
    main()
