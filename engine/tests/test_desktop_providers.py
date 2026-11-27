import json
import os
import sys
import unittest
from pathlib import Path
from threading import Event, Thread
from time import monotonic
from unittest.mock import Mock, patch

import requests

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import load_sites
from http_workers import NetworkPool
from native_profiles import EXTRA, desktop_check


class ApiTests(unittest.TestCase):
    def check(self,name,handle,data,code=200,location='',retry=False):
        response=requests.Response()
        response.status_code=code
        response.url='https://fixture.example/profile'
        response._content=json.dumps(data).encode()
        response.headers.update({'Content-Type':'application/json','Location':location})
        network=Mock()
        from contextlib import nullcontext
        session=Mock()
        session.get.return_value=response
        network.session.return_value=nullcontext(session)
        row=desktop_check('enhanced',name,(load_sites()|EXTRA)[name],handle,3,network,retry)
        self.assertEqual(session.get.call_count,1)
        return row,session.get.call_args.args[0]

    def test_bluesky_short_custom_and_mismatch(self):
        for value,normalized in [('blue','blue.bsky.social'),('blue.example','blue.example')]:
            row,url=self.check('Bluesky',value,{'handle':normalized,'did':'did:plc:fixture'})
            self.assertEqual(row['status'],'found')
            self.assertTrue(url.endswith('actor='+normalized))
            self.assertTrue(row['url'].endswith('/'+normalized))
        self.assertEqual(self.check('Bluesky','blue',{'handle':'other','did':'did:plc:fixture'})[0]['status'],'inconclusive')
        self.assertEqual(self.check('Bluesky','blue',{'error':'ProfileNotFound'},400)[0]['status'],'not_found')

    def test_lichess_and_crates_positive_negative_and_denials(self):
        for name,data in [('Scratch',{'username':'Blue','id':33}),('Lichess',{'username':'Blue','id':'blue'}),('crates.io',{'user':{'login':'Blue','id':31}}),('Chess.com',{'username':'Blue','player_id':17}),('GitHub',{'login':'Blue','id':3}),('GitLab',[{'username':'Blue','id':4}])]:
            self.assertEqual(self.check(name,'blue',data)[0]['status'],'found')
            self.assertEqual(self.check(name,'blue',{},404)[0]['status'],'not_found')
            self.assertEqual(self.check(name,'other',data)[0]['status'],'inconclusive')
            self.assertEqual(self.check(name,'blue',data,429,retry=True)[0]['status'],'blocked')

    def test_osu_expected_and_unrelated_redirect(self):
        self.assertEqual(self.check('osu!','blue',{},302,'/users/123')[0]['status'],'possible')
        self.assertEqual(self.check('osu!','blue',{},302,'https://different.invalid/users/123')[0]['status'],'inconclusive')

    def test_supervisor_reaps_stalled_worker(self):
        import socketserver
        release=Event()
        class Slow(socketserver.BaseRequestHandler):
            def handle(self):
                release.wait(5)
        class Server(socketserver.ThreadingTCPServer):
            daemon_threads=True
        with Server(('127.0.0.1',0),Slow) as server:
            url='https://fixture.invalid/profile'
            Thread(target=server.serve_forever,daemon=True).start()
            with patch.dict(os.environ,{'HTTPS_PROXY':f'http://127.0.0.1:{server.server_address[1]}','https_proxy':f'http://127.0.0.1:{server.server_address[1]}','no_proxy':'','NO_PROXY':''}):
                try:
                    with NetworkPool(1) as pool, pool.session([url]) as session:
                        started=monotonic()
                        with self.assertRaises(requests.Timeout):
                            session.get(url,timeout=1)
                        self.assertLess(monotonic()-started,6)
                finally:
                    release.set()
                    server.shutdown()

    def test_proxy_denial_stops_deep_fallback_without_attributing_origin_http(self):
        from discovery import directory, run_profile
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread
        calls = []
        class Deny(BaseHTTPRequestHandler):
            def do_CONNECT(self):
                calls.append(1)
                self.send_error(403)
            def log_message(self, *args):
                pass
        item = directory(load_sites(), False, False)['Bluesky']
        with ThreadingHTTPServer(('127.0.0.1', 0), Deny) as server:
            proxy = f'http://127.0.0.1:{server.server_port}'
            Thread(target=server.serve_forever, daemon=True).start()
            try:
                with patch.dict(os.environ, {'HTTPS_PROXY':proxy, 'https_proxy':proxy, 'no_proxy':'', 'NO_PROXY':''}), NetworkPool(1) as pool:
                    row = run_profile('deep', 'Bluesky', item, 'fixture', 4, pool, True)
            finally:
                server.shutdown()
        self.assertEqual(row['status'], 'blocked')
        self.assertNotIn('http', row)
        self.assertEqual(len(calls), 1)

    def test_cold_worker_startup_is_inside_the_request_deadline(self):
        from time import sleep
        fake = Mock()
        def start_worker(*args, **kwargs):
            sleep(.08)
            return fake
        fake.output.get.return_value = b'{"failure":"connection"}'
        with patch('http_workers.Worker', start_worker), NetworkPool(1) as pool:
            with self.assertRaises(requests.Timeout):
                pool.request({'timeout':.04})
        fake.process.stdin.write.assert_not_called()
