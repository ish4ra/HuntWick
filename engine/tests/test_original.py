import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import requests

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ENGINE))
import providers


class OriginalTests(unittest.TestCase):
    def test_unmodified_cli_and_original_over_real_local_http(self):
        class Site(BaseHTTPRequestHandler):
            def respond(self):
                code = 403 if '/denial/' in self.path else 404 if '/missing/' in self.path else 200
                self.send_response(code)
                self.send_header('Content-Type','text/html')
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(b'<title>Welcome</title>')
                methods.append(self.command)
            do_GET = do_HEAD = respond
            def log_message(self,*args): pass

        methods = []
        with ThreadingHTTPServer(('127.0.0.1',0),Site) as server, tempfile.TemporaryDirectory() as tmp:
            Thread(target=server.serve_forever,daemon=True).start()
            origin=f'http://127.0.0.1:{server.server_port}'
            rules={n:{'urlMain':origin,'url':origin+'/'+n+'/{}','errorType':'status_code',
                      'username_claimed':'fixture'} for n in ('exists','missing','denial')}
            rules['denial'].update(errorType='message',errorMsg='unknown account')
            path=Path(tmp)/'manifest.json'
            path.write_text(json.dumps(rules))
            env={**os.environ,'NO_PROXY':'127.0.0.1','HTTPS_PROXY':'http://127.0.0.1:9','NETRC':os.devnull}
            subprocess.run([sys.executable,'-m','sherlock_project.sherlock','fixture','--json',str(path),
                            '--ignore-exclusions','--print-all','--folderoutput',tmp,'--csv','--no-color'],
                           env=env,check=True,capture_output=True,timeout=30)
            with (Path(tmp)/'fixture.csv').open() as f:
                expected={r['name']:r['exists'] for r in csv.DictReader(f)}
            stock_methods=sorted(methods);methods.clear()
            # Only substitute the production HTTPS-origin guard for this loopback fixture.
            with patch.object(providers,'PublicSession',lambda urls: requests.Session()):
                rows={n:providers.original(n,r,'fixture',3) for n,r in rules.items()}
            server.shutdown()
            self.assertEqual({n:r['verdict'] for n,r in rows.items()},expected)
            self.assertEqual(stock_methods,sorted(methods))
            self.assertEqual(stock_methods,['GET','HEAD','HEAD'])
            self.assertEqual([rows[n]['status'] for n in rules],['provider_match','not_found','conflict'])
