"""Compile public-profile rules from the exact Maigret wheel used by the desktop."""
import gzip
import hashlib
import json
import re
from importlib.metadata import distribution
from pathlib import Path
from urllib.parse import urlsplit

from maigret import MaigretDatabase

DATA = Path(__file__).parent / 'data'
UPSTREAM = '99e70fe7167b1c884a221d41f8a1815e40ca1db7a07581b6b401fd590e5b6fa4'
# Reviewed read-only profile template families and individually reviewed public routes.
ENGINES = {'GitLab', 'Gitea', 'Discourse', 'DiscourseJson', 'Flarum', 'Mastodon', 'Lemmy'}
INDIVIDUAL = {'GitHub', 'GitLab', 'Codewars', 'RubyGems', 'Codédex', 'Bluesky', 'MyAnimeList', 'Scratch', 'Replit', 'Meendo', 'Open Game Art', 'HackingWithSwift', 'Hack MD', 'Codementor'}
ADULT = {'erotic', 'porn', 'webcam'}
GROUPS = [('Gaming', {'gaming', 'sport'}), ('Development', {'coding', 'tech'}),
          ('Creative', {'art', 'design', 'photo', 'music'}), ('Forums', {'discussion', 'forum'})]


def public_host(url):
    p = urlsplit(url)
    host = p.hostname or ''
    if (p.scheme == 'https' and re.fullmatch(r'(?:[a-z0-9-]+\.)+[a-z]{2,63}', host)
            and not host.endswith(('.local', '.internal', '.onion', '.lan', '.home', '.localhost'))
            and not (p.username or p.password or p.port or p.fragment)
            and not re.search(r'[\s\\]', url)):
        return host.removeprefix('www.')
    return None


def compile_catalog():
    wheel = distribution('maigret')
    raw = wheel.locate_file('maigret/resources/data.json').read_bytes()
    if wheel.version != '0.6.7' or hashlib.sha256(raw).hexdigest() != UPSTREAM:
        raise ValueError('Unexpected upstream Maigret snapshot')
    db = MaigretDatabase().load_from_json(json.loads(raw))
    entries, unavailable = {}, {}
    for s in db.sites:
        tags = set(s.tags)
        reason = ''
        if s.disabled:
            reason = 'Disabled by Maigret.'
        elif s.type != 'username' or s.similar_search or s.source:
            reason = 'Requires a different identifier, similar-name search or mirror.'
        elif s.engine not in ENGINES and s.name not in INDIVIDUAL:
            reason = 'Public username route has not been reviewed.'
        elif (s.protection or s.activation or s.protocol or s.headers or s.ignore403 or
              s.request_method.upper() not in {'', 'GET', 'HEAD'} or s.get_params or s.request_payload
              or tags & {'tor', 'i2p', 'cybercriminal'}):
            reason = 'Requires an unsupported transport, header or access policy.'
        else:
            def expand(template):
                return template.format(urlMain=s.url_main.rstrip('/'), urlSubpath=s.url_subpath,
                                       username='{}')
            profile = expand(s.url)
            probe = expand(s.url_probe or s.url)
            host = public_host(s.url_main)
            if not host or not all(t.count('{}') == 1 and public_host(t) in {host, 'api.'+host, 'public.api.'+host}
                                   for t in (profile, probe)):
                reason = 'Requires an unsupported public profile route.'
            else:
                # Only reviewed family paths may be inherited. Per-instance
                # overrides are separately reviewed before becoming eligible.
                if s.engine in ENGINES:
                    template = db.engines_dict[s.engine].site
                    if profile != expand(template['url']) or probe != expand(template.get('urlProbe', template['url'])):
                        reason = 'Instance overrides the reviewed profile route.'
                if not reason:
                    rule = {k:v for k,v in s.json.items() if k in {
                        'checkType','regexCheck','requestMethod','requestHeadOnly','encoding','presenseStrs',
                        'absenceStrs','tags'}}
                    rule.update(url=profile.replace('{}','{username}'),urlMain=s.url_main,
                                urlProbe=probe.replace('{}','{username}'),errors=s.errors_dict)
                    category = ('Adult (NSFW)' if tags & ADULT else
                                next((g for g, t in GROUPS if tags & t),
                                     'Development' if s.engine in {'GitLab','Gitea'} else 'Forums' if s.engine else 'Other'))
                    entries[s.name] = {'rule':rule,'category':category}
        if reason:
            unavailable[s.name] = reason
    return {'total':len(db.sites),'upstreamEnabled':sum(not s.disabled for s in db.sites),
            'entries':entries,'unavailable':unavailable}


if __name__ == '__main__':
    data = json.dumps(compile_catalog(), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    (DATA / 'maigret.json.gz').write_bytes(gzip.compress(data, mtime=0))
    print(hashlib.sha256(data).hexdigest())
