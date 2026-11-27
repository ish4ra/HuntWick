"""Plan desktop searches by public profile, keeping each provider's evidence."""
from concurrent.futures import wait, FIRST_COMPLETED
from time import monotonic
from urllib.parse import urlsplit

import requests

from catalog import describe
from http_workers import NetworkPool
from maigret_provider import check, eligible, snapshot
from native_profiles import EXTRA, NATIVE, native
from providers import original


def profile_key(url):
    p = urlsplit(url)
    path = p.path.rstrip('/')
    if path == '/u/{}/summary':
        path = '/u/{}'
    return (p.hostname.removeprefix('www.'), path, p.query)


def directory(sherlock, adult, experimental):
    merged = {}
    for name, rule in (sherlock | EXTRA).items():
        item = {'base':rule}
        if name in sherlock:
            item['sherlock'] = sherlock[name]
        if name in NATIVE:
            item['native'] = NATIVE[name]
        merged[name] = item
    profiles = {profile_key(item['base']['url']):name for name,item in merged.items()}
    for upstream, rule in eligible(adult,experimental).items():
        key = profile_key(rule['url'])
        name = profiles.get(key)
        if name is None:
            name = upstream if upstream not in merged else upstream+' (Maigret)'
            profiles[key] = name
            merged[name] = {'base':rule}
        merged[name].setdefault('maigret', []).append((upstream,rule))
    return merged


def modes(item):
    result = ['deep']
    if 'sherlock' in item:
        result.append('sherlock')
    if 'sherlock' in item or 'native' in item:
        result.append('enhanced')
    if 'maigret' in item:
        result.append('maigret')
    return result


def catalog(items, version):
    result = describe({name:item['base'] for name,item in items.items()},version)
    for row in result['sites']:
        row['engines'] = modes(items[row['name']])
    unavailable = {r['name']:r['reason'] for r in result['unavailable']}
    unavailable['SpankBang'] = 'No public username rule in the bundled Sherlock or Maigret catalogs.'
    for name, reason in snapshot()['unavailable'].items():
        if name not in items:
            unavailable.setdefault(name,reason)
    result['unavailable'] = [dict(name=n,reason=r) for n,r in unavailable.items()]
    result.update(databaseVersion=result['databaseVersion']+' + Maigret 0.6.7',updatedAt='2026-11-26')
    return result


class SharedNetwork:
    """Short-lived cache for one profile. Never share responses across targets or runs."""
    session = NetworkPool.session

    def __init__(self, network):
        self.network = network
        self.responses = {}
        self.failures = {}

    def request(self, command):
        # Use one anonymous user agent across the Deep run. Content negotiation
        # and non-default headers remain part of the cache key.
        headers = {k.lower():v for k,v in command['headers'].items()
                   if k.lower() not in {'user-agent','accept-encoding','connection'}}
        headers.setdefault('accept','*/*')
        headers['user-agent'] = 'HuntWick public profile lookup'
        key = (command['url'],command['method'],tuple(sorted(headers.items())),bool(command['redirect']))
        failure_key = (command['method'], command['url'])
        if failure_key in self.failures:
            raise self.failures[failure_key]
        if key not in self.responses:
            try:
                res = self.network.request({**command, 'headers':headers})
            except (requests.Timeout, requests.ConnectionError) as exc:
                self.failures[failure_key] = exc
                raise
            self.responses[key] = res
            if res.url == command['url'] and not 300 <= res.status_code < 400:
                self.responses[key[:-1]+(not key[-1],)] = res
        return self.responses[key]


def reconcile(reports):
    order = ['conflict','found','provider_match','possible','not_found','blocked','timed_out','error','inconclusive']
    best = dict(min(reports,key=lambda r:order.index(r['status'])))
    statuses = {r['status'] for r in reports}
    if 'not_found' in statuses and statuses & {'found','provider_match','possible'}:
        best['status'] = 'conflict'
    best['sources'] = [{k:r[k] for k in ('provider','verdict','status','http','elapsedMs','message') if k in r}
                       for r in reports]
    if len(reports) > 1:
        best['message'] = ' · '.join(r['provider']+' '+r.get('verdict',r['status']) for r in reports)
    return best


def run_profile(mode, name, item, username, timeout, network, retry):
    started = monotonic()
    calls = []
    if mode in {'enhanced','deep'} and 'native' in item:
        calls.append((native,name,item['native']))
    # The two pinned templates only accept the short bsky.social prefix.
    # A dotted handle already identifies its domain; the native API accepts it.
    exact_domain = mode == 'deep' and name == 'Bluesky' and '.' in username
    if not exact_domain and 'sherlock' in item and (mode in {'sherlock','deep'} or mode=='enhanced' and not calls):
        calls.append((original,name,item['sherlock']))
    if not exact_domain and mode in {'maigret','deep'}:
        calls.extend((check,n,rule) for n,rule in item.get('maigret',[]))

    def attempt():
        shared = SharedNetwork(network) if mode=='deep' else network
        reports = []
        for index, (fn, provider_name, rule) in enumerate(calls):
            remaining = timeout - (monotonic()-attempt_start)
            if remaining <= 0:
                break
            # Spend the remainder on the last method. Leave each pending
            # complementary provider a share if the current socket stalls.
            budget = remaining / (len(calls) - index)
            row = fn(provider_name,rule,username,budget,shared)
            reports.append(row)
            transient = (row.get('http') is None and
                         (row['status'] == 'timed_out' or 'Connection failure' in
                          (row.get('verdict'), row.get('message'))))
            if transient:
                continue
            if (row['status'] in {'blocked','timed_out','error'} or row.get('http') in {401,403,407,429,451}
                    or 'Conflicting evidence: blocked' in row.get('message','')):
                break
        return reconcile(reports) if mode == 'deep' else reports[0]

    attempt_start = monotonic()
    row = attempt()
    if retry and row.get('http') is None and (row['status']=='timed_out' or
            'Connection failure' in (row.get('message'),row.get('verdict'))):
        attempt_start = monotonic()
        row = attempt()
        row['message'] = 'Retried once. '+row.get('message',row.get('verdict',''))
    return dict(row,platform=name,elapsedMs=round((monotonic()-started)*1000))


def stream(pool, names, size, submit):
    # Admit only enough work to keep the supervised HTTP workers occupied.
    names = iter(names)
    active = {submit(pool,n) for _,n in zip(range(size), names)}
    while active:
        done, active = wait(active,return_when=FIRST_COMPLETED)
        for job in done:
            yield job.result()
            name = next(names,None)
            if name is not None:
                active.add(submit(pool,name))
