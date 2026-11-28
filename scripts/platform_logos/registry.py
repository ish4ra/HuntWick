"""Generate local UI lookups and audit the same offline directories the engine exposes."""
import argparse
import csv
from collections import Counter
from hashlib import sha256
from importlib.metadata import distribution
from io import StringIO
import json
from pathlib import Path
import re
import sys
import unicodedata
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ART = ROOT / 'public/platforms'
sys.path.insert(0, str(ROOT / 'engine'))
from catalog import load_sites
from discovery import catalog, directory

MAIGRET_DATA = '99e70fe7167b1c884a221d41f8a1815e40ca1db7a07581b6b401fd590e5b6fa4'
FAMILIES = {k: k.lower() for k in ('GitLab', 'Gitea', 'Mastodon', 'Lemmy', 'Flarum', 'Discourse')}
FAMILIES['DiscourseJson'] = 'discourse'
# Maigret 0.6.7 uses the compatible Gitea detector for Forgejo. These instances
# also appear on the Forgejo community's published list (see the maintenance guide).
OVERRIDES = dict.fromkeys(('git.disroot.org', 'git.gay', 'bolha.dev', 'forgejo.it'), 'forgejo')
FALLBACK = 'No reviewed matching brand asset or supported family in the pinned metadata.'


def normalized(s):
    s = unicodedata.normalize('NFKD', s.strip().lower())
    return re.sub('[^a-z0-9]', '', s)


def check_art(path):
    data = path.read_bytes()
    if path.suffix == '.png':
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'Invalid PNG {path.name}')
        return
    root = ElementTree.fromstring(data)
    tags = {tag.tag.rsplit('}', 1)[-1] for tag in root.iter()}
    allowed = {'svg','path','defs','g','circle','ellipse','rect','polygon','polyline','line','title',
               'desc','linearGradient','radialGradient','stop','clipPath','mask'}
    viewbox = [float(x) for x in root.attrib.get('viewBox','').replace(',',' ').split()]
    if (root.tag != '{http://www.w3.org/2000/svg}svg' or len(viewbox) != 4
            or min(viewbox[2:]) <= 0 or tags - allowed or not tags & {'path','circle','polygon','rect'}):
        raise ValueError(f'Invalid SVG {path.name}: {tags - allowed}')
    for node in root.iter():
        for k,v in node.attrib.items():
            if (k.startswith('on') or k.rsplit('}',1)[-1] in ('href','style') or
                    ('url(' in v and not re.fullmatch(r'url\(#[\w-]+\)',v))):
                raise ValueError(f'External or active content in {path.name}')


def brand_index():
    labels, brands, assets = {}, {}, set()
    with (ART / 'credits.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            path = ART / row['asset']
            if path.parent != ART or sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'Incorrect asset {path.name}')
            check_art(path)
            slug = path.stem
            assets.add(path.name)
            labels[slug] = row['brand']
            for name in [slug, row['brand'], *row['aliases'].split('|')]:
                if not name:
                    continue
                key = normalized(name)
                if brands.setdefault(key, slug) != slug:
                    raise ValueError(f'Ambiguous brand alias {name}')
    dark = ART / 'laracasts-dark.svg'
    check_art(dark)
    if sha256(dark.read_bytes()).hexdigest() != 'b25a7d24f7d19ebcb3c7719faab40d7c76662609068cd0052e031432ac4676a7':
        raise ValueError('Incorrect Laracasts dark asset')
    if {p.name for p in ART.iterdir() if p.suffix in {'.svg','.png'}} != assets | {dark.name}:
        raise ValueError('Unregistered local artwork')
    return brands, labels


def upstream():
    wheel = distribution('maigret')
    data = wheel.locate_file('maigret/resources/data.json').read_bytes()
    if wheel.version != '0.6.7' or sha256(data).hexdigest() != MAIGRET_DATA:
        raise ValueError('Review the changed upstream Maigret family metadata')
    return json.loads(data)['sites']


def artifacts():
    brands, labels = brand_index()
    source = upstream()
    full = directory(load_sites(True, True), True, True)
    default = directory(load_sites(False, False), False, False)
    owner_scope = directory(load_sites(True, False), True, False)
    unavailable = {r['name'] for r in catalog(full, '')['unavailable']} - full.keys()
    instances = {}
    reasons = json.loads((HERE/'review.json').read_text(encoding='utf-8'))
    counts = {name: Counter() for name in ('all_bundled','default','adult_enabled','unavailable')}
    family_counts = Counter()
    out = StringIO()
    writer = csv.writer(out,lineterminator='\n')
    writer.writerow(['platform','scope','default','adult_enabled','resolution','logo','evidence'])
    for name in sorted(full.keys() | unavailable, key=lambda s:(s.casefold(),s)):
        item = full.get(name,{})
        aliases = [alias for alias,_ in item.get('maigret',[])]
        aliases.extend(item.get('base',{}).get('aliases',{}))
        slug = brands.get(normalized(name))
        why = ''
        if name.lower() in OVERRIDES:
            slug, mode, why = OVERRIDES[name.lower()], 'family', 'Reviewed Forgejo instance list'
        elif slug:
            mode = 'direct' if name.casefold() == labels[slug].casefold() else 'alias'
            why = labels[slug]
        else:
            matches = {brands[normalized(a)] for a in aliases if normalized(a) in brands}
            if len(matches) == 1:
                slug = matches.pop()
                mode, why = 'alias', 'Provider alias for the same profile'
            else:
                families = {FAMILIES[s['engine']] for a in [name, *aliases]
                            if (s := source.get(a, {})).get('engine') in FAMILIES}
                if len(families) == 1:
                    slug = families.pop()
                    mode, why = 'family', 'Pinned Maigret engine identity'
                else:
                    mode, why = 'fallback', reasons.get(name,FALLBACK)
        if slug:
            if slug not in labels:
                raise ValueError(f'Unknown asset {slug}')
            if mode == 'family' or normalized(name) not in brands:
                instances[name.lower()] = slug
            for a in aliases:
                if a not in full and normalized(a) not in brands:
                    instances.setdefault(a.lower(),slug)
        scope = 'all_bundled' if name in full else 'unavailable'
        counts[scope][mode] += 1
        if name in default: counts['default'][mode] += 1
        if name in owner_scope: counts['adult_enabled'][mode] += 1
        if mode == 'family' and name in full: family_counts[slug] += 1
        writer.writerow([name,scope,int(name in default),int(name in owner_scope),mode,slug or '',why])
    counts = {scope:{**c,'total':sum(c.values()),'actual_logos':sum(c.values())-c['fallback']}
              for scope,c in counts.items()}
    stats = {'scopes':counts,'brand_assets':len(labels),'bundled_family_inheritance':family_counts}
    return {
        ROOT/'docs/platform-logos/catalog.csv': out.getvalue(),
        ROOT/'docs/platform-logos/coverage.json': json.dumps(stats,sort_keys=True,indent=2)+'\n',
        ROOT/'src/platformLogos.generated.json': json.dumps({'brands':brands,'instances':instances},
                                                             sort_keys=True,ensure_ascii=False,indent=1)+'\n',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the published registry and coverage without writing')
    args = parser.parse_args()
    for p,content in artifacts().items():
        if args.check and (not p.is_file() or p.read_text(encoding='utf-8') != content):
            raise SystemExit(f'Outdated generated file {p.relative_to(ROOT)}')
        if not args.check:
            p.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
