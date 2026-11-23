"""Build a self-contained engine folder on the OS/architecture that will run it."""
from importlib import metadata
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'build'
DEST = ROOT / 'dist'
NAME = 'huntwick-engine'


def copy_notices(target):
    shutil.copytree(ROOT / 'notices', target, dirs_exist_ok=True)
    python_license = next((path for path in (
        Path(sysconfig.get_path('stdlib')) / 'LICENSE.txt',
        Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'LICENSE',
    ) if path.is_file()), None)
    if python_license is None:
        raise RuntimeError('Unable to locate the Python interpreter license')
    shutil.copyfile(python_license, target / 'Python-LICENSE.txt')
    for dist in metadata.distributions():
        # Keep nested notices (for example NumPy's compiled dependencies) and
        # both common spellings of licence. Always preserve original file bytes.
        for path in dist.files or ():
            if not any(part.endswith('.dist-info') for part in path.parts):
                continue
            if ('licenses' not in path.parts and not path.name.lower().startswith(
                    ('license', 'licence', 'copying', 'copyright', 'notice', 'authors'))):
                continue
            source = Path(dist.locate_file(path))
            if source.is_file() and not path.is_absolute() and '..' not in path.parts:
                destination = target / 'python-packages' / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)


def main():
    WORK.mkdir(exist_ok=True)
    # mypyc-compiled tomli wheels import a platform-specific top-level module
    # from native code. PyInstaller's Python import analysis cannot see it.
    hidden = []
    for path in metadata.distribution('tomli').files or ():
        if len(path.parts) == 1 and '__mypyc.' in path.name:
            hidden.extend(['--hidden-import', path.name.split('.')[0]])
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
        *hidden, '--noupx', '--name', NAME, '--distpath', str(DEST), '--workpath', str(WORK),
        '--specpath', str(WORK), '--copy-metadata', 'sherlock-project',
        '--add-data', f'{ROOT / "data"}:data', str(ROOT / 'adapter.py'),
    ], check=True)
    copy_notices(DEST / NAME / 'notices')


if __name__ == '__main__':
    main()
