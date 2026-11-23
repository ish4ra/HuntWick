"""Launch an installed HuntWick desktop and wait for its native/webview check."""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    executable = parser.parse_args().executable.resolve(strict=True)
    env = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    # WebKit and WebView2 can need native OS helpers during startup.
    if os.name == "nt":
        windows = Path(env["SystemRoot"])
        env["PATH"] = os.pathsep.join(map(str, (windows / "System32", windows)))
    else:
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            [str(executable), "--verify-install"], env=env, cwd=directory,
            timeout=90, check=True,
        )
    print(f"{executable} verified the installed catalog and rendered search form.")


if __name__ == "__main__":
    main()
