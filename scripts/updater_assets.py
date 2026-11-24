"""Stage native Tauri update archives and assemble a release manifest."""
import json
from pathlib import Path
import subprocess
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / 'package.json').read_text())['version']
TARGETS = {
    'x86_64-pc-windows-msvc': ('windows-x86_64', 'nsis/*.exe'),
    'x86_64-unknown-linux-gnu': ('linux-x86_64', 'appimage/*.AppImage'),
    'aarch64-apple-darwin': ('darwin-aarch64', 'macos/*.app.tar.gz'),
    'x86_64-apple-darwin': ('darwin-x86_64', 'macos/*.app.tar.gz'),
}

def stage(target):
    platform, pattern = TARGETS[target]
    bundle = ROOT / 'src-tauri/target' / target / 'release/bundle'
    source, = bundle.glob(pattern)
    subprocess.run(["node", "scripts/verify-update.mjs", source, VERSION], check=True)
    signature = Path(str(source) + '.sig').read_text().strip()
    if not signature:
        raise ValueError('Missing Tauri signature')
    out = ROOT / 'installers' / target
    name = f'HuntWick-{VERSION}-{target}' + ''.join(Path(pattern).suffixes)
    shutil.copyfile(source, out / name)
    (out / (name + '.sig')).write_text(signature)
    entry = {'signature': signature, 'url': f'https://github.com/ish4ra/HuntWick/releases/download/v{VERSION}/{name}'}
    (out / (platform+'.json')).write_text(json.dumps(entry))

def manifest():
    out = ROOT / 'installers'
    platforms = {p:json.loads((out/(p+'.json')).read_text()) for p,_ in TARGETS.values()}
    data = {'version':VERSION,'notes':(ROOT/'CHANGELOG.md').read_text().split('\n## ',2)[1][:3000], 'platforms':platforms}
    (out/'latest.json').write_text(json.dumps(data, indent=2)+'\n')

if __name__ == '__main__':
    manifest() if sys.argv[1] == 'manifest' else stage(sys.argv[1])
