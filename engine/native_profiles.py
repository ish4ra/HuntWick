"""Read only the identity fields required for a public profile lookup."""
import re
from urllib.parse import urljoin, urlsplit

import requests

from providers import HOST_LABEL, http_warning, original

PROVIDER = 'HuntWick public lookup'
NATIVE = {'Bluesky', 'Lichess', 'osu!', 'crates.io'}
EXTRA = {'crates.io': {'url':'https://crates.io/users/{}','urlMain':'https://crates.io',
                       'nativeOnly':True,'category':'Development'}}


def native(name, rule, username, timeout, network):
    handle = username.lower()
    profile = rule['url'].format(username)
    row = {'type':'result','platform':name,'url':profile,'provider':PROVIDER,'status':'inconclusive'}
    if name == 'Bluesky':
        handle = handle if '.' in handle else handle+'.bsky.social'
        if not all(HOST_LABEL.fullmatch(part) for part in handle.split('.')) or not handle.split('.')[-1][0].isalpha():
            return {**row,'verdict':'Invalid handle'}
        profile = 'https://bsky.app/profile/'+handle
        row['url'] = profile
        probe = 'https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor='+handle
    elif name == 'Lichess':
        probe = 'https://lichess.org/api/user/'+handle+'?trophies=false'
    elif name == 'crates.io':
        probe = 'https://crates.io/api/v1/users/'+handle
    else:
        probe = profile
    headers = {'User-Agent':'HuntWick public profile lookup (+https://github.com/ish4ra/HuntWick)',
               'Accept':'text/html' if name=='osu!' else 'application/json'}
    try:
        with network.session([probe]) as session:
            res = session.get(probe,headers=headers,allow_redirects=False,timeout=timeout)
    except requests.Timeout:
        return {**row,'status':'timed_out','verdict':'Timeout'}
    except requests.ConnectionError as exc:
        return {**row,'status':'error','verdict':'TLS failure' if isinstance(exc,requests.exceptions.SSLError) else 'Connection failure'}
    except requests.RequestException:
        return {**row,'status':'error','verdict':'Request failed'}
    row['http'] = res.status_code
    warning = http_warning(res)
    if name == 'osu!' and res.status_code in {301,302,307,308}:
        dest = urlsplit(urljoin(profile,res.headers.get('Location','')))
        if dest.netloc=='osu.ppy.sh' and dest.scheme=='https' and re.fullmatch(r'/users/[1-9][0-9]*/?',dest.path) and not (dest.query or dest.fragment):
            return {**row,'status':'possible','verdict':'Numeric profile redirect','url':dest.geturl()}
    if warning:
        return {**row,'status':warning,'verdict':f'HTTP {res.status_code}'}
    try:
        data = res.json() if 'json' in res.headers.get('Content-Type','').lower() else {}
    except (ValueError,RecursionError):
        data = {}
    if not isinstance(data,dict):
        data = {}
    if name=='Bluesky' and res.status_code==400 and data.get('error')=='ProfileNotFound':
        return {**row,'status':'not_found','verdict':'ProfileNotFound'}
    if res.status_code != 200:
        return {**row,'verdict':f'HTTP {res.status_code}'}
    if name=='Bluesky':
        verified = (str(data.get('handle','')).lower()==handle and
                    re.fullmatch(r'did:(?:plc|web):[a-zA-Z0-9.:%_-]+',str(data.get('did',''))))
    elif name=='Lichess':
        verified = data.get('id')==handle and str(data.get('username','')).lower()==handle
    elif name=='crates.io':
        user = data.get('user')
        verified = isinstance(user,dict) and type(user.get('id')) is int and user['id']>0 and str(user.get('login','')).lower()==handle
    else:
        verified = False
    return {**row,'status':'found' if verified else 'inconclusive',
            'verdict':'API identity matched' if verified else 'Identity unavailable'}


def desktop_check(mode, name, rule, username, timeout, network, retry):
    from time import monotonic
    started = monotonic()
    provider = native if mode=='enhanced' and name in NATIVE else original
    row = provider(name, rule, username, timeout, network)
    if retry and (row['status']=='timed_out' and row.get('http') is None or row.get('verdict')=='Connection failure'):
        row = provider(name, rule, username, timeout, network)
        row['message'] = 'Retried once. '+row.get('message',row.get('verdict',''))
    row['elapsedMs'] = round((monotonic()-started)*1000)
    return row
