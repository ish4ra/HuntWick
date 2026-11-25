"""Desktop providers. Sherlock owns its rules, request methods and verdicts."""
import os
import re
from time import monotonic
from types import FunctionType, SimpleNamespace
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from sherlock_project.notify import QueryNotify
from sherlock_project.result import QueryStatus

from evidence import GATE_PATH, GATE_TITLE, ProfileHead

MAX_BYTES = 512 * 1024
HOST_LABEL = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', re.I)


class PublicAdapter(HTTPAdapter):
    """Apply the byte limit at each HTTP hop, before Requests buffers content."""
    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        try:
            media = response.headers.get('Content-Type', '').lower()
            if media.startswith(('audio/', 'video/', 'image/', 'application/octet-stream')):
                raise requests.RequestException('Unsupported media')
            body = bytearray()
            for chunk in response.iter_content(16384):
                if len(body) + len(chunk) > MAX_BYTES:
                    raise requests.RequestException('Profile document exceeds the size limit')
                body.extend(chunk)
            response._content = bytes(body)
            response._content_consumed = True
            return response
        finally:
            response.close()


class PublicSession(requests.Session):
    def __init__(self, urls):
        super().__init__()
        self.trust_env = False
        self.max_redirects = 4
        self.hosts = {urlsplit(url).hostname.lower().removeprefix('www.') for url in urls}
        self.mount('https://', PublicAdapter())

    def send(self, request, **kwargs):
        dest = urlsplit(request.url)
        if (dest.scheme != 'https' or dest.username or dest.password or dest.port
                or dest.hostname.lower().removeprefix('www.') not in self.hosts):
            raise requests.RequestException('Redirect outside the platform')
        for header in ('Cookie','Authorization','Proxy-Authorization'):
            request.headers.pop(header, None)
        kwargs['verify'] = os.getenv('REQUESTS_CA_BUNDLE') or os.getenv('CURL_CA_BUNDLE') or True
        kwargs['proxies'] = requests.utils.get_environ_proxies(request.url)
        return super().send(request, **kwargs)


def sherlock_report(name, rule, username, timeout):
    from sherlock_project import sherlock as core
    urls = [rule.get('urlProbe', rule['url']).format(username), rule['url'].format(username)]
    with PublicSession(urls) as session:
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


def original(name, definition, username, timeout):
    started = monotonic()
    rule = dict(definition)
    profile = rule['url'].format(username)
    event = {'type':'result','platform':name,'url':profile,'provider':'Sherlock Original','status':'inconclusive'}
    if any('{}' in urlsplit(url).netloc and not HOST_LABEL.fullmatch(username)
           for url in (rule['url'],rule.get('urlProbe',rule['url']))):
        return {**event,'message':'Handle cannot be used as a public host label.'}
    report = sherlock_report(name, rule, username, timeout)
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
