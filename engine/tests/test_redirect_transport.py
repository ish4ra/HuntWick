"""Loopback-only Deep benchmark with identical profile routes and ground truth."""
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import socketserver
import ssl
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
from time import monotonic
import unittest
from unittest.mock import Mock, patch

import requests
from urllib3.exceptions import ReadTimeoutError

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
from http_workers import PublicAdapter

# Each route uses the bundled Maigret Discourse JSON method. The fixture answers
# all TLS connections locally and has no facility to forward a request.
ROUTES = {
    'MetaDiscourse': ('meta.discourse.org', True, False),
    'discourse.ubuntu.com': ('discourse.ubuntu.com', False, False),
    'Rust-lang': ('users.rust-lang.org', True, True),
    'internals.rust-lang.org': ('internals.rust-lang.org', False, True),
}


def measure(engine, repeats, timeout=1):
    hosts = {host: (present, redirect) for host, present, redirect in ROUTES.values()}
    finished = Event()
    with TemporaryDirectory() as tmp:
        cert, key = (Path(tmp) / name for name in ('ca.pem', 'key.pem'))
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-days', '1', '-subj', '/CN=HuntWick local fixture',
                        '-addext', 'subjectAltName=' + ','.join('DNS:' + h for h in hosts),
                        '-keyout', str(key), '-out', str(cert)], check=True, capture_output=True)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)

        class Fixture(socketserver.StreamRequestHandler):
            def handle(self):
                target = self.rfile.readline().split()
                if len(target) != 3 or target[0] != b'CONNECT':
                    return
                host = target[1].decode().removesuffix(':443')
                if host not in hosts:
                    return
                while self.rfile.readline().strip():
                    pass
                self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
                with context.wrap_socket(self.connection, server_side=True) as tls, tls.makefile('rb') as stream:
                    method, path, _ = stream.readline().split()
                    while stream.readline().strip():
                        pass
                    present, redirect = hosts[host]
                    if method != b'GET' or path not in {b'/u/fixture.json', b'/canonical/fixture.json'}:
                        raise ValueError('Unexpected fixture request')
                    if redirect and path == b'/u/fixture.json':
                        tls.sendall(b'HTTP/1.1 302 Found\r\nLocation: /canonical/fixture.json\r\n'
                                    b'Content-Length: 1\r\nConnection: close\r\n\r\n')
                        # The Location is complete. The intermediate body never arrives
                        # within the profile deadline.
                        finished.wait(timeout + 3)
                        return
                    code = b'200 OK' if present else b'404 Not Found'
                    body = b'{"user":{"username":"fixture","id":7}}' if present else b'{"error":"missing"}'
                    tls.sendall(b'HTTP/1.1 ' + code + b'\r\nContent-Type: application/json\r\n'
                                b'Connection: close\r\nContent-Length: ' + str(len(body)).encode() +
                                b'\r\n\r\n' + body)

        with socketserver.ThreadingTCPServer(('127.0.0.1', 0), Fixture) as server:
            proxy = 'http://127.0.0.1:' + str(server.server_address[1])
            env = {k:v for k,v in os.environ.items() if k.lower() not in
                   {'https_proxy', 'all_proxy', 'no_proxy', 'pythonpath', 'pythonhome'}}
            env.update(HTTPS_PROXY=proxy, REQUESTS_CA_BUNDLE=str(cert), OPENBLAS_NUM_THREADS='1')
            Thread(target=server.serve_forever, daemon=True).start()
            request = dict(op='search', providerMode='deep', sites=list(ROUTES),
                           username='fixture', timeout=timeout, concurrency=1, retryTransient=False)
            try:
                for _ in range(repeats):
                    start = monotonic()
                    raw = subprocess.check_output([sys.executable, str(engine / 'adapter.py')],
                                                  input=json.dumps(request).encode() + b'\n',
                                                  env=env, timeout=30)
                    elapsed = round((monotonic() - start) * 1000)
                    *rows, done = map(json.loads, raw.splitlines())
                    assert done == {'type':'done'} and len(rows) == len(ROUTES)
                    yield elapsed, {r['platform']:r['status'] for r in rows}
            finally:
                finished.set()
                server.shutdown()


class RedirectTransportTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('openssl'), 'loopback TLS fixture requires openssl')
    def test_slow_redirect_body_does_not_hide_the_final_profile(self):
        expected = {name:'provider_match' if present else 'not_found'
                    for name, (_, present, _) in ROUTES.items()}
        for _, statuses in measure(ENGINE, 1, timeout=5):
            self.assertEqual(statuses, expected)

    def test_unfollowed_redirect_keeps_body_for_provider_verdict(self):
        response = requests.Response()
        response.status_code = 302
        response.headers['Location'] = '/another-page'
        response.raw = Mock()
        response.raw.stream.return_value = [b'An upstream absence marker']
        with closing(PublicAdapter()) as adapter, patch('requests.adapters.HTTPAdapter.send', return_value=response):
            result = adapter.send(requests.Request('GET', 'https://fixture.invalid').prepare())
        self.assertEqual(result.content, b'An upstream absence marker')

    def test_streamed_read_timeout_is_a_timeout(self):
        response = requests.Response()
        response.raw = Mock()
        response.raw.stream.side_effect = ReadTimeoutError(None, None, 'fixture')
        adapter = PublicAdapter()
        try:
            with patch('requests.adapters.HTTPAdapter.send', return_value=response):
                with self.assertRaises(requests.Timeout):
                    adapter.send(requests.Request('GET', 'https://fixture.invalid').prepare())
        finally:
            adapter.close()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--benchmark':
        for elapsed, statuses in measure(Path(sys.argv[2]).resolve(), 3):
            print(json.dumps(dict(wallMs=elapsed, results=statuses)), flush=True)
    else:
        unittest.main()
