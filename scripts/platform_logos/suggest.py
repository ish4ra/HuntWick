"""Find candidate matches in a downloaded pinned icon package. Never assigns by guess."""
import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import tarfile

from registry import ROOT, normalized


def candidates(path):
    with tarfile.open(path, 'r:*') as archive:
        names = set(archive.getnames())
        if 'package/icons.json' in names:
            data = json.load(archive.extractfile('package/icons.json'))
            if isinstance(data,dict) and isinstance(data.get('icons'),dict):
                return list(data['icons'])
        if 'package/data/simple-icons.json' in names:
            return [i['title'] for i in json.load(archive.extractfile('package/data/simple-icons.json'))]
        return [PurePosixPath(name).stem.removeprefix('brand-').removeprefix('cib-')
                for name in sorted(names) if name.endswith('.svg') and (
                    '/brands/' in name or '/brand/' in name or '/brand-' in name)]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archives',nargs='+',type=Path)
    args=parser.parse_args()
    with (ROOT/'docs/platform-logos/catalog.csv').open(encoding='utf-8',newline='') as file:
        rows=[r for r in csv.DictReader(file) if r['scope']=='all_bundled' and r['resolution']=='fallback']
    for archive in args.archives:
        names={normalized(n):n for n in candidates(archive)}
        for row in rows:
            n=row['platform']
            if normalized(n) in names:
                print(f"{n}\t{archive.name}\t{names[normalized(n)]}")
