"""Validate identities returned by pinned, public instance-local lookup routes."""

import requests

from http_workers import connection_status
from providers import http_warning

LOOKUPS = {
    '/api/v1/accounts/lookup?acct={username}': 'mastodon',
    '/api/v3/user?username={username}': 'lemmy',
}


def family(rule):
    origin = rule['urlMain'].rstrip('/')
    template = rule['maigretRule'].get('urlProbe', '')
    return LOOKUPS.get(template.removeprefix(origin)) if template.startswith(origin + '/') else None


def check(name, rule, username, timeout, network):
    kind = family(rule)
    url = rule['maigretRule']['urlProbe'].format(username=username)
    profile = rule['url'].format(username)
    row = dict(type='result', platform=name, url=profile, provider='HuntWick public lookup')
    try:
        response = network.request(dict(url=url, origins=[url], method='GET', headers={'Accept':'application/json'},
                                        timeout=timeout, redirect=False))
    except requests.Timeout:
        return dict(row, status='timed_out', verdict='Timeout')
    except requests.ConnectionError as exc:
        status, verdict = connection_status(exc)
        return dict(row, status=status, verdict=verdict)
    except requests.RequestException:
        return dict(row, status='error', verdict='Request failed')
    code = response.status_code
    row['http'] = code
    warning = http_warning(response)
    if warning and warning != 'not_found':
        return dict(row, status=warning, verdict=f'HTTP {code}')
    unknown = dict(row, status='inconclusive', verdict='Identity unavailable')
    if 'application/json' not in response.headers.get('Content-Type','').lower():
        return unknown
    try:
        data = response.json()
    except (ValueError, RecursionError):
        return unknown
    if not isinstance(data,dict):
        return unknown
    if code == 404 and isinstance(data.get('error'),str) and data['error'].lower() in {
        'record not found','not_found','couldnt_find_person','could_not_find_person'}:
        return dict(row,status='not_found',verdict='HTTP 404')
    if code != 200:
        return unknown
    if kind == 'mastodon':
        handle, account, actor = data.get('username'), data.get('acct'), data.get('url')
        local = isinstance(account,str) and account.casefold() == username.casefold()
        identifier = data.get('id')
        valid_id = isinstance(identifier,str) and identifier.isascii() and identifier.isdecimal() and identifier.strip('0')
    else:
        view = data.get('person_view')
        person = view.get('person') if isinstance(view,dict) else None
        if not isinstance(person,dict):
            return unknown
        handle, local, actor = person.get('name'), person.get('local') is True, person.get('actor_id') or person.get('ap_id')
        valid_id = type(person.get('id')) is int and person['id'] > 0 and not person.get('deleted')
    if not (local and valid_id and isinstance(handle,str) and handle.casefold() == username.casefold()):
        return unknown
    if not isinstance(actor,str) or actor.rstrip('/').casefold() != profile.rstrip('/').casefold():
        return unknown
    return dict(row,status='found',verdict='API identity matched')
