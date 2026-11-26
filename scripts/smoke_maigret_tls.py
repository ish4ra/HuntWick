"""Test the frozen Maigret verdict path with a verified, loopback-only TLS fixture."""
import json
import os
from pathlib import Path
import socketserver
import ssl
import subprocess
import tempfile
from threading import Thread


def verify(executable):
    with tempfile.TemporaryDirectory() as tmp:
        cert, key = (Path(tmp)/name for name in ('ca.pem','key.pem'))
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
            '-subj','/CN=api.github.com','-addext','subjectAltName=DNS:api.github.com',
            '-keyout',str(key),'-out',str(cert)],check=True,capture_output=True)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert,key)

        class Fixture(socketserver.StreamRequestHandler):
            def handle(self):
                if self.rfile.readline().split()[:2] != [b'CONNECT',b'api.github.com:443']:
                    return
                while self.rfile.readline().strip():
                    pass
                self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
                with ctx.wrap_socket(self.connection,server_side=True) as tls:
                    stream = tls.makefile('rb')
                    path = stream.readline().split()[1]
                    while stream.readline().strip():
                        pass
                    code = b'200 OK' if path == b'/users/synthetic-present' else b'404 Not Found'
                    tls.sendall(b'HTTP/1.1 '+code+b'\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}')
        with socketserver.ThreadingTCPServer(('127.0.0.1',0),Fixture) as server:
            Thread(target=server.serve_forever,daemon=True).start()
            env = {k:v for k,v in os.environ.items() if k.lower() not in
                   {'https_proxy','all_proxy','no_proxy','virtual_env','pythonpath','pythonhome'}}
            env.update(PATH=tmp,REQUESTS_CA_BUNDLE=str(cert),HTTPS_PROXY=f'http://127.0.0.1:{server.server_address[1]}')
            try:
                for handle,expected in [('synthetic-present','Claimed'),('synthetic-absent','Available')]:
                    req = dict(op='search',providerMode='maigret',sites=['GitHub'],username=handle,timeout=4,concurrency=1)
                    data = subprocess.check_output([executable],input=json.dumps(req).encode()+b'\n',cwd=tmp,env=env,timeout=40)
                    row, done = map(json.loads,data.splitlines())
                    if (row['provider'],row['verdict'],done['type']) != ('Maigret',expected,'done'):
                        raise ValueError('Frozen Maigret TLS verdict mismatch')
            finally:
                server.shutdown()


if __name__ == '__main__':
    import sys
    verify(Path(sys.argv[1]).resolve())
