"""HuntWick's one-request NDJSON adapter for the official Sherlock library."""
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import json
import os
import re
import sys
from time import monotonic
from urllib.parse import urljoin, urlsplit

import requests
from sherlock_project import __version__, sherlock as sherlock_core
from sherlock_project.notify import QueryNotify
from urllib3.exceptions import ReadTimeoutError

from catalog import describe, load_sites
from evidence import classify, equivalent

MAX_BODY = 512 * 1024
HANDLE = re.compile(r'[a-zA-Z0-9_.-]{1,64}')
HOST_LABEL = re.compile(r'(?i)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?')


def fetch(url, timeout):
    # Reads only a bounded prefix. A same-profile www/trailing-slash redirect is
    # common. Other redirects are evidence for classification, never new targets.
    deadline = monotonic() + timeout
    with requests.Session() as session:
        session.trust_env = False  # never load .netrc credentials for public probes
        for attempt in range(2):
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise requests.Timeout()
            with session.get(url, headers={'User-Agent': 'HuntWick/0.1 (public profile lookup)'},
                             proxies=requests.utils.get_environ_proxies(url),
                             verify=os.getenv('REQUESTS_CA_BUNDLE') or os.getenv('CURL_CA_BUNDLE') or True,
                             allow_redirects=False, timeout=remaining, stream=True) as response:
                if response.is_redirect and not attempt:
                    target = urljoin(url, response.headers['Location'])
                    if target != url and equivalent(url, target):
                        session.cookies.clear()
                        url = target
                        continue
                content = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    if monotonic() >= deadline:
                        raise requests.Timeout()
                    content.extend(chunk[:MAX_BODY - len(content)])
                    if len(content) >= MAX_BODY:
                        break
                response._content = bytes(content)
                response._content_consumed = True
                return response


class ProfileSession:
    """Sherlock 0.16.2 transport slot; the outer executor owns concurrency.

    Sherlock consumes a requests Response via Future.result(). Providing a
    completed future lets it apply its site rules unchanged after our bounded
    anonymous GET. Each outer worker checks one site and owns one session.
    """
    def __init__(self, *, session, max_workers):
        session.close()

    def get(self, *, url, timeout, **kwargs):
        future = Future()
        try:
            future.set_result(fetch(url, timeout))
        except requests.RequestException as exc:
            future.set_exception(exc)
        return future


# This executable is the only consumer, with Sherlock pinned in uv.lock.
sherlock_core.SherlockFuturesSession = ProfileSession


def check_site(name, definition, username, timeout):
    profile = definition['url'].replace('{}', username)
    result = {'type': 'result', 'platform': name, 'url': profile, 'status': 'inconclusive'}
    for template in (definition['url'], definition.get('urlProbe', definition['url'])):
        if '{}' in urlsplit(template).netloc and not HOST_LABEL.fullmatch(username):
            return result
    # Sherlock attaches the future to this dictionary. Never share it across runs.
    rule = {**definition, 'request_method': 'GET'}
    try:
        report = sherlock_core.sherlock(username, {name: rule}, QueryNotify(), timeout=timeout)
        future = rule.get('request_future')
        if future is None:  # platform-specific username syntax
            return result
        response = future.result()
        result['status'] = classify(rule, profile, username, report[name]['status'].status, response)
    except requests.Timeout:
        result['status'] = 'timed_out'
    except requests.ConnectionError as exc:
        # requests wraps urllib3's streaming read timeout as ConnectionError.
        result['status'] = 'timed_out' if any(isinstance(arg, ReadTimeoutError) for arg in exc.args) else 'error'
    except Exception:
        # Isolate malformed and failing sites. Never send response bodies, error
        # strings (which can include the URL) or tracebacks to application logs.
        result['status'] = 'error'
    return result


def bounded_integer(request, key, default, upper):
    value = request.get(key, default)
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f'{key} must be an integer between 1 and {upper}.')
    return value


def events(request, sites):
    if not isinstance(request, dict):
        raise ValueError('Expected a JSON object.')
    if request.get('op') == 'catalog':
        yield describe(sites, __version__)
    elif request.get('op') == 'search':
        username = request.get('username')
        if not isinstance(username, str) or not HANDLE.fullmatch(username) or username in {'.', '..'}:
            raise ValueError('Invalid username.')
        selected = request.get('sites')
        if (not isinstance(selected, list) or not 1 <= len(selected) <= len(sites)
                or any(not isinstance(name, str) or name not in sites for name in selected)
                or len(selected) != len(set(selected))):
            raise ValueError('Select unique platforms from the bundled catalog.')
        timeout = bounded_integer(request, 'timeout', 10, 60)
        concurrency = bounded_integer(request, 'concurrency', 8, 20)
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            jobs = [pool.submit(check_site, name, sites[name], username, timeout) for name in selected]
            for job in as_completed(jobs):
                yield job.result()
    else:
        raise ValueError('Unknown operation.')
    yield {'type': 'done'}


def main():
    try:
        line = sys.stdin.buffer.readline(65537)
        if len(line) > 65536:
            raise ValueError('Request exceeds size limit.')
        try:
            request = json.loads(line)
        except (ValueError, RecursionError):
            raise ValueError('Invalid JSON request.') from None
        for event in events(request, load_sites()):
            print(json.dumps(event, separators=(',', ':')), flush=True)
        return 0
    except (OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else 'Cannot read bundled engine resources.'
        print(json.dumps({'type': 'error', 'message': message}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
