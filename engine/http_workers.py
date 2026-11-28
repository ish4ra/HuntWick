"""Anonymous, size-limited Requests I/O in reusable, interruptible processes."""
import base64
import json
import os
import re
from pathlib import Path
from queue import Queue, Empty
import subprocess
import sys
from threading import Thread
from time import monotonic
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import NameResolutionError, ReadTimeoutError

MAX_BYTES = 512 * 1024


class ProxyDenied(requests.ConnectionError):
    """The configured proxy rejected CONNECT before the origin responded."""


class DnsFailure(requests.ConnectionError):
    """The resolver could not supply a network address."""


def connection_status(exc):
    if isinstance(exc, ProxyDenied):
        return 'blocked', 'Proxy denied connection'
    if isinstance(exc, requests.exceptions.ProxyError):
        return 'error', 'Proxy connection failure'
    if isinstance(exc, DnsFailure):
        return 'error', 'DNS failure'
    if isinstance(exc, requests.exceptions.SSLError):
        return 'error', 'TLS failure'
    return 'error', 'Connection failure'


class PublicAdapter(HTTPAdapter):
    """Apply the byte limit at each HTTP hop, before Requests buffers content."""
    def __init__(self, *, follow_redirects=False):
        super().__init__()
        self.follow_redirects = follow_redirects

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if self.follow_redirects and response.is_redirect:
            # Requests needs Location for the next, separately guarded hop.
            # Close the unread socket before marking the empty body consumed.
            response.close()
            response._content = b''
            response._content_consumed = True
            return response
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
        except requests.ConnectionError as exc:
            if any(isinstance(arg, ReadTimeoutError) for arg in exc.args):
                raise requests.ReadTimeout('Profile body read timed out') from None
            raise
        finally:
            response.close()


class PublicSession(requests.Session):
    def __init__(self, urls, *, follow_redirects=False):
        super().__init__()
        self.trust_env = False
        self.max_redirects = 4
        self.hosts = {urlsplit(url).hostname.lower().removeprefix('www.') for url in urls}
        self.mount('https://', PublicAdapter(follow_redirects=follow_redirects))

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


def exchange(command):
    with PublicSession(command['origins'], follow_redirects=command['redirect']) as session:
        response = session.request(command['method'], command['url'], headers=command['headers'],
                                   timeout=command['timeout'], allow_redirects=command['redirect'])
        return {'url':response.url,'code':response.status_code,'encoding':response.encoding,
                'headers':{k:v for k,v in response.headers.items() if k.lower() in
                           ('location','content-type','cf-mitigated','retry-after')},
                'body':base64.b64encode(response.content).decode('ascii')}


def worker_main():
    incoming = Queue()
    def read_commands():
        for line in sys.stdin.buffer:
            incoming.put(line)
        os._exit(0)  # Supervisor exited, including during DNS or a blocking read.
    Thread(target=read_commands, daemon=True).start()
    print('ready', flush=True)
    while True:
        command = json.loads(incoming.get())
        try:
            result = exchange(command)
        except requests.Timeout:
            result = {'failure':'timeout'}
        except requests.exceptions.SSLError:
            result = {'failure':'tls'}
        except requests.exceptions.ProxyError as exc:
            cause = getattr(exc.args[0], 'reason', None)
            tunnel = getattr(cause, 'original_error', None)
            denied = re.match(r'^Tunnel connection failed: (401|403|407|429|451)\b', str(tunnel))
            result = {'failure': 'proxy_denied' if denied else 'proxy'}
        except requests.ConnectionError as exc:
            cause = getattr(exc.args[0], 'reason', None)
            result = {'failure':'dns' if isinstance(cause, NameResolutionError) else 'connection'}
        except Exception:
            result = {'failure':'request'}
        print(json.dumps(result), flush=True)


class Worker:
    def __init__(self, startup_timeout):
        command = ([sys.executable,'--http-worker'] if getattr(sys,'frozen',False) else
                   [sys.executable,'-E','-B',str(Path(__file__).resolve())])
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, close_fds=True)
        self.output = Queue()
        def read():
            for line in self.process.stdout:
                self.output.put(line)
            self.output.put(b'')
        self.reader = Thread(target=read,daemon=True)
        self.reader.start()
        try:
            if self.output.get(timeout=min(20, startup_timeout)).strip() != b'ready':
                raise OSError('Public request worker failed to start')
        except BaseException:
            self.close()
            raise

    def close(self):
        self.process.kill()
        self.process.wait()
        self.reader.join()
        self.process.stdin.close()
        self.process.stdout.close()


class NetworkPool:
    """One slot per active site. Kill and reap a stalled socket or resolver."""
    def __init__(self, size):
        self.idle = Queue()
        for _ in range(size):
            self.idle.put(None)

    def __enter__(self):
        return self

    def __exit__(self,*args):
        while not self.idle.empty():
            worker = self.idle.get()
            if worker:
                worker.close()

    def request(self, command):
        deadline = monotonic() + command['timeout']
        try:
            worker = self.idle.get(timeout=command['timeout'])
        except Empty:
            raise requests.Timeout('No available public request worker') from None
        try:
            if worker is None:
                worker = Worker(max(0, deadline - monotonic()))
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise Empty()
            worker.process.stdin.write(json.dumps({**command, 'timeout': remaining}).encode()+b'\n')
            worker.process.stdin.flush()
            data = worker.output.get(timeout=max(0, deadline - monotonic()))
            if not data:
                raise OSError('Public request worker closed')
            result = json.loads(data)
        except (Empty,OSError,ValueError) as exc:
            if worker:
                worker.close()
                worker = None
            if isinstance(exc,Empty):
                raise requests.Timeout('Active request deadline') from None
            raise requests.RequestException('Public request worker failed') from None
        finally:
            self.idle.put(worker)
        failure = result.get('failure')
        if failure:
            error = {'timeout':requests.Timeout,'tls':requests.exceptions.SSLError,
                     'proxy_denied':ProxyDenied,'proxy':requests.exceptions.ProxyError,'dns':DnsFailure,
                     'connection':requests.ConnectionError}.get(failure,requests.RequestException)
            raise error('Public request failed')
        response = requests.Response()
        response.status_code = result['code']
        response.url = result['url']
        response.encoding = result['encoding']
        response.headers.update(result['headers'])
        response._content = base64.b64decode(result['body'])
        response._content_consumed = True
        return response

    def session(self, urls):
        pool = self
        class WorkerSession(requests.Session):
            def send(self, request, **kwargs):
                response = pool.request({'url':request.url,'origins':urls,'method':request.method,
                                         'headers':dict(request.headers),'timeout':kwargs['timeout'],
                                         'redirect':kwargs.get('allow_redirects',True)})
                return requests.hooks.dispatch_hook('response', request.hooks, response, **kwargs)
        session = WorkerSession()
        session.trust_env = False
        return session


if __name__ == '__main__':
    worker_main()
