"""Verify extracted production artifacts and prepare the exact public feed files offline."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from updater_assets import ROOT, TARGETS, VERSION, manifest

RC3_FINGERPRINT = 'cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669'


def prepare():
    out = ROOT / 'installers'
    fingerprint = hashlib.sha256(os.environ['HUNTWICK_ARTIFACT_PUBLIC_KEY'].strip().encode()).hexdigest()
    if fingerprint != RC3_FINGERPRINT:
        raise ValueError('Candidate does not match the installed RC.3 trust anchor.')
    checksums = []
    for target,(platform,pattern) in TARGETS.items():
        checksums.extend((out/f'SHA256SUMS-{target}.txt').read_text().splitlines())
        filename = f'HuntWick-{VERSION}-{target}' + ''.join(Path(pattern).suffixes)
        subprocess.run(['node','scripts/verify-update.mjs',out/filename,VERSION],check=True)
        expected = {'url':f'https://github.com/ish4ra/HuntWick/releases/download/v{VERSION}/{filename}',
                    'signature':(out/(filename+'.sig')).read_text().strip()}
        if json.loads((out/(platform+'.json')).read_text()) != expected:
            raise ValueError(f'Updater metadata differs from verified payload for {target}.')
    (out/'SHA256SUMS').write_text('\n'.join(sorted(checksums))+'\n')
    subprocess.run(['sha256sum','--check','--strict','SHA256SUMS'],cwd=out,check=True)
    manifest()
    (out/'candidate.json').write_text(json.dumps({'version':VERSION,'commit':os.environ['GITHUB_SHA'],
        'run':os.environ['GITHUB_RUN_ID'],'updaterKeySha256':fingerprint},indent=2)+'\n')


if __name__=='__main__':
    prepare()
