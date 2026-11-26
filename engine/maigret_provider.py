"""Desktop-only adapter for the pinned Maigret single-site request and verdict API."""
from functools import cache
import gzip
from hashlib import sha256
import json
import logging
from time import monotonic

import requests

from catalog import DATA
from providers import http_warning

VERSION = 'Maigret 0.6.7'
DIGEST = '9c16c00861a15e144b76e73205db0b698196332abcbddbcfa1185f092fb079aa'
logger = logging.Logger('huntwick.maigret')
logger.disabled = True


@cache
def snapshot():
    raw = gzip.decompress((DATA / 'maigret.json.gz').read_bytes())
    if sha256(raw).hexdigest() != DIGEST:
        raise ValueError('Bundled Maigret catalog integrity check failed.')
    return json.loads(raw)


@cache
def eligible(adult=False, experimental=False):
    sherlock = json.loads((DATA / 'sites.json').read_bytes())
    excluded = set((DATA / 'exclusions.txt').read_text().casefold().splitlines())
    adult_names = {name.casefold() for name, rule in sherlock.items() if isinstance(rule,dict) and rule.get('isNSFW')}
    entries = {}
    for name, item in snapshot()['entries'].items():
        restricted = item['category'] == 'Adult (NSFW)' or name.casefold() in adult_names
        if (restricted and not adult) or (name.casefold() in excluded and not experimental):
            continue
        rule = item['rule']
        entries[name] = {'url': rule['url'].replace('{username}', '{}'), 'urlMain':rule['urlMain'],
                         'category':'Adult (NSFW)' if restricted else item['category'], 'maigretRule':rule}
    return entries


class RequestParameters:
    def prepare(self, **kwargs):
        return kwargs


def check(name, definition, username, timeout, network):
    from maigret.checking import make_site_result, process_site_result
    from maigret.sites import MaigretSite

    started = monotonic()
    site = MaigretSite(name, definition['maigretRule'])
    options = dict(parsing=False, forced=False, id_type='username', timeout=timeout,
                   checkers={'': RequestParameters()})
    info = make_site_result(site, username, options, logger)
    row = {'type':'result','platform':name,'url':definition['url'].format(username),
           'provider':'Maigret','status':'inconclusive'}
    if 'status' in info:
        return {**row,'verdict':info['status'].status.value,'elapsedMs':0}
    params = info['future']
    try:
        response = network.request(dict(url=params['url'], origins=[params['url']],
            method=params['method'].upper(), headers={'User-Agent':'HuntWick public profile lookup'},
            timeout=timeout, redirect=params['allow_redirects']))
        text = response.content.decode(params['encoding'] or response.encoding or 'utf-8', errors='replace')
        verdict = process_site_result((text,response.status_code,None),None,logger,info,site)['status'].status.value
        warning = http_warning(response)
        status = {'Claimed':'provider_match','Available':'not_found'}.get(verdict,'inconclusive')
        row.update(verdict=verdict, http=response.status_code, status=warning or status)
        if verdict == 'Claimed' and warning == 'not_found':
            row['status'] = 'conflict'
    except requests.Timeout:
        row.update(status='timed_out',message='Request timed out.')
    except requests.exceptions.SSLError:
        row.update(status='error',message='TLS failure')
    except requests.ConnectionError:
        row.update(status='error',message='Connection failure')
    except (requests.RequestException, LookupError, ValueError):
        row.update(status='error',message='Public request failed.')
    row['elapsedMs'] = round((monotonic()-started)*1000)
    return row
