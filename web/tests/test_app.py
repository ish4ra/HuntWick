import asyncio
import base64
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import httpx

from web.app import Limits, create_app


class HostedTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pid_file = Path(self.tmp.name) / 'pid'
        self.request = {'id':'test-one','username':'with_underscore','sites':['GitHub','GitLab'], 'timeout':10,'concurrency':2}
        self.auth = ('huntwick', 'fixture-pass')
        self.client = self.setup_app()
        await self.client.get('/api/catalog')

    def setup_app(self, mode='ok', password='fixture-pass', **limits):
        command = (sys.executable, str(Path(__file__).with_name('fixture_engine.py')), mode, str(self.pid_file))
        root = Path(self.tmp.name) / 'dist'
        root.mkdir(exist_ok=True)
        (root / 'index.html').write_text('test ui')
        (root / 'assets').mkdir(exist_ok=True)
        (root / 'assets' / 'entry.js').write_text('ok()')
        self.app = create_app(password=password, command=command, static=root, limits=replace(Limits(), **limits))
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://testserver', auth=self.auth)
        self.addAsyncCleanup(client.aclose)
        return client

    async def test_catalog_auth_and_files(self):
        self.assertEqual((await self.client.get('/healthz', auth=None)).json(), {'status':'ok'})
        for route in ['/', '/api/catalog', '/assets/entry.js']:
            res = await self.client.get(route, auth=None)
            self.assertEqual(res.status_code,401)
            self.assertIn('Basic',res.headers['www-authenticate'])
        self.assertEqual((await self.client.get('/assets/entry.js')).status_code,200)
        for route in ['/api/docs','/docs','/catalog.json','/assets/%2e%2e/%2e%2e/engine/data/sites.json']:
            self.assertEqual((await self.client.get(route)).status_code,404)
        cat = await self.client.get('/api/catalog')
        self.assertEqual([s['name'] for s in cat.json()['sites']], ['GitHub','GitLab'])
        self.assertEqual(cat.headers['cache-control'],'no-store')
        closed = self.setup_app(password='')
        self.assertEqual((await closed.get('/api/catalog')).status_code,503)

    async def test_validate_and_deny_cross_origin_before_launch(self):
        for changes in [{'sites':['https://example.org']},{'sites':['GitLab','GitLab']},{'username':['one','two']},{'username':'../private'},{'concurrency':3},{'timeout':False},{'id':'../escape'},{'url':'https://example.org'}]:
            response=await self.client.post('/api/search', json=self.request|changes)
            self.assertEqual(response.status_code,400, changes)
        self.assertEqual((await self.client.post('/api/search',json=self.request,headers={'Origin':'https://other.example'})).status_code,403)
        self.assertEqual((await self.client.post('/api/search',content='x' * 5000,headers={'Content-Type':'application/json'})).status_code,413)
        self.assertEqual((await self.client.post('/api/search',data={'username':'abc'})).status_code,415)
        self.assertFalse(self.pid_file.exists())

    async def test_stream_results_and_rate_limit(self):
        client=self.setup_app(searches_per_client=1)
        response=await client.post('/api/search',json=self.request)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.headers['content-type'].startswith('application/x-ndjson'))
        frames=[json.loads(line) for line in response.text.splitlines()]
        self.assertEqual([f['type'] for f in frames],['result','result','done'])
        self.assertEqual({f['id'] for f in frames},{'test-one'})
        self.assertEqual((await client.post('/api/search',json=self.request, headers={'X-Forwarded-For':'198.51.100.1'})).status_code,429)
        self.assertFalse(self.app.state.jobs.active)

    async def test_untrusted_child_result_is_not_exposed(self):
        client=self.setup_app(mode='bad')
        response=await client.post('/api/search',json=self.request)
        self.assertEqual(response.json()['type'],'error')
        self.assertNotIn('example.org',response.text)

    async def test_deadline_reaps_child(self):
        client=self.setup_app(mode='block', deadline=1)
        res=await client.post('/api/search',json=self.request)
        frames=[json.loads(line) for line in res.text.splitlines()]
        self.assertEqual([f.get('status',f['type']) for f in frames],['inconclusive','timed_out','done'])
        self.assert_reaped()

    def assert_reaped(self):
        self.assertFalse(self.app.state.jobs.active)
        if os.name == 'posix':
            with self.assertRaises(ProcessLookupError):
                os.kill(int(self.pid_file.read_text()),0)

    async def open_stream(self, client):
        await client.get('/api/catalog')
        recv, sent = asyncio.Queue(), asyncio.Queue()
        await recv.put({'type':'http.request','body':json.dumps(self.request).encode(),'more_body':False})
        headers = [(b'authorization',b'Basic '+base64.b64encode(b'huntwick:fixture-pass')),(b'content-type',b'application/json'),(b'host',b'testserver'),(b'cookie','; '.join(f'{k}={v}' for k,v in client.cookies.items()).encode())]
        scope={'type':'http','asgi':{'version':'3.0','spec_version':'2.4'},'http_version':'1.1','method':'POST','path':'/api/search','raw_path':b'/api/search','scheme':'http','query_string':b'','headers':headers,'client':('127.0.0.1',23456),'server':('testserver',80)}
        task=asyncio.create_task(self.app(scope,recv.get,sent.put))
        self.assertEqual((await asyncio.wait_for(sent.get(),2))['status'],200)
        first=await asyncio.wait_for(sent.get(),3)
        self.assertEqual(json.loads(first['body'])['platform'],'GitHub')
        return recv,sent,task

    async def test_disconnect_reaps_running_child(self):
        client=self.setup_app(mode='block')
        recv,sent,task=await self.open_stream(client)
        await recv.put({'type':'http.disconnect'})
        await asyncio.wait_for(task,2)
        self.assert_reaped()

    async def test_cancellation_owned_and_active_limit(self):
        client=self.setup_app(mode='block', active_global=1)
        recv,sent,task=await self.open_stream(client)
        other=httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://testserver',auth=self.auth)
        async with other:
            self.assertEqual((await other.post('/api/search/test-one/cancel',json={})).status_code,404)
            self.assertEqual((await other.post('/api/search',json=self.request|{'id':'second'})).status_code,429)
        self.assertEqual((await client.post('/api/search/test-one/cancel',json={})).status_code,204)
        await asyncio.wait_for(task,2)
        self.assertEqual(json.loads((await sent.get())['body'])['status'],'cancelled')
        self.assert_reaped()
