"""Desktop providers. Sherlock owns its rules, request methods and verdicts."""
import re
from time import monotonic
from types import FunctionType, SimpleNamespace
from urllib.parse import urlsplit

import requests
from http_workers import PublicSession
from sherlock_project.notify import QueryNotify
from sherlock_project.result import QueryStatus

from evidence import GATE_PATH, GATE_TITLE, ProfileHead

HOST_LABEL = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', re.I)


def sherlock_report(name, rule, username, timeout, network):
    from sherlock_project import sherlock as core
    urls = [rule.get('urlProbe', rule['url']).format(username), rule['url'].format(username)]
    with (network.session(urls) if network else PublicSession(urls)) as session:
        # Sherlock 0.16.2 has no session parameter. Bind only its session factory
        # per invocation. Its futures, request construction and verdict code are upstream.
        context = SimpleNamespace(session=lambda: session)

        original = core.sherlock
        check = FunctionType(original.__code__, {**original.__globals__, 'requests': context},
                             original.__name__, original.__defaults__, original.__closure__)
        return check(username, {name:rule}, QueryNotify(), timeout=timeout)[name]


def http_warning(response):
    code = response.status_code
    if code in {401,403,407,429,451} or response.headers.get('cf-mitigated','').lower() == 'challenge':
        return 'blocked'
    if code in {404,410}:
        return 'not_found'
    if code in {408,504}:
        return 'timed_out'
    if code >= 500:
        return 'error'
    if 300 <= code < 400:
        return 'inconclusive'
    head = ProfileHead()
    if 'html' in response.headers.get('Content-Type','').lower():
        try:
            head.feed(response.text)
        except (ValueError, AssertionError):
            return 'inconclusive'
    if head.gated or GATE_PATH.search(urlsplit(response.url).path) or GATE_TITLE.search(head.title.strip()):
        return 'blocked'
    return None


def original(name, definition, username, timeout, network=None):
    started = monotonic()
    rule = dict(definition)
    profile = rule['url'].format(username)
    event = {'type':'result','platform':name,'url':profile,'provider':'Sherlock Original','status':'inconclusive'}
    if any('{}' in urlsplit(url).netloc and not HOST_LABEL.fullmatch(username)
           for url in (rule['url'],rule.get('urlProbe',rule['url']))):
        return {**event,'message':'Handle cannot be used as a public host label.'}
    report = sherlock_report(name, rule, username, timeout, network)
    verdict = report['status'].status
    event['verdict'] = verdict.value
    future = rule.get('request_future')
    try:
        if future is not None:
            response = future.result()
            event['http'] = response.status_code
            warning = http_warning(response)
            if verdict is QueryStatus.CLAIMED:
                event['status'] = 'conflict' if warning else 'provider_match'
            elif warning:
                event['status'] = warning
            elif verdict is QueryStatus.AVAILABLE:
                event['status'] = 'not_found'
            elif verdict is QueryStatus.WAF:
                event['status'] = 'blocked'
            event['message'] = 'Sherlock reported '+verdict.value+'. HTTP '+str(response.status_code)+'.'
            if warning and verdict is QueryStatus.CLAIMED:
                event['message'] += ' Conflicting evidence: '+warning.replace('_',' ')+'.'
        else:
            event['message'] = 'Username does not fit this platform rule.'
    except requests.Timeout:
        event.update(status='timed_out',message='Request timed out.')
    except requests.RequestException:
        event.update(status='error',message='The public request could not be completed.')
    event['elapsedMs'] = round((monotonic()-started)*1000)
    return event
