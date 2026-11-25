"""Anonymous, size-limited Requests I/O in reusable, interruptible processes."""
import base64
import json
import os
from pathlib import Path
from queue import Queue, Empty
import subprocess
import sys
from threading import Thread
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter

MAX_BYTES = 512 * 1024


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


def exchange(command):
    with PublicSession(command['origins']) as session:
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
        except requests.ConnectionError:
            result = {'failure':'connection'}
        except Exception:
            result = {'failure':'request'}
        print(json.dumps(result), flush=True)


class Worker:
    def __init__(self):
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
            if self.output.get(timeout=20).strip() != b'ready':
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
        worker = self.idle.get()
        try:
            if worker is None:
                worker = Worker()
            worker.process.stdin.write(json.dumps(command).encode()+b'\n')
            worker.process.stdin.flush()
            data = worker.output.get(timeout=command['timeout'])
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
