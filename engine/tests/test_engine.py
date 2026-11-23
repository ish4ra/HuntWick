import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
import adapter


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites = adapter.load_sites()

    def run_search(self, name='GitHub', username='blue', code=200, body='', headers=None, failure=None):
        def fetch(url, timeout):
            if failure:
                raise failure
            response = requests.Response()
            response.url = url
            response.status_code = code
            response._content = body.encode()
            response.headers.update({'Content-Type': 'text/html', **(headers or {})})
            return response

        with patch.object(adapter, 'fetch', side_effect=fetch):
            request = {'op': 'search', 'username': username, 'sites': [name], 'timeout': 3, 'concurrency': 1}
            self.assertEqual(len(rows := list(adapter.events(request, self.sites))), 2)
            self.assertEqual(rows[1], {'type': 'done'})
            self.assertEqual((rows[0]['type'], rows[0]['platform']), ('result', name))
            return rows[0]['status']

    def test_catalog_protocol_works_offline(self):
        proc = subprocess.run([sys.executable, str(ENGINE / 'adapter.py')], input=b'{"op":"catalog"}\n', capture_output=True, check=True)
        catalog, done = map(json.loads, proc.stdout.splitlines())
        self.assertEqual((catalog['type'], catalog['version'], done), ('catalog', '0.16.2', {'type': 'done'}))
        names = {s['name'] for s in catalog['sites']}
        self.assertGreater(len(names), 300)
        self.assertNotIn('Reddit', names)  # bundled upstream exclusions
        self.assertIn('GitHub', names)
        self.assertTrue(all(s['url'].startswith('https://') for s in catalog['sites']))

    def test_strong_html_identity(self):
        self.assertEqual(self.run_search(body='<meta name="octolytics-dimension-user_login" content="Blue">'), 'found')
        self.assertEqual(self.run_search(body='<meta name="octolytics-dimension-user_login" content="SomeoneElse">'), 'inconclusive')

    def test_json_identity(self):
        self.assertEqual(self.run_search(name='GitLab', body='[{"id": 418, "username":"Blue"}]', headers={'Content-Type':'application/json'}), 'found')
        self.assertEqual(self.run_search(name='GitLab', body='[{"username":"blueish"}]', headers={'Content-Type':'application/json'}), 'inconclusive')

    def test_weak_and_generic_responses(self):
        for body in ('', '<html>Welcome to GitHub</html>', '<title>blue</title>', 'Hello blue', '<title>Page not found | blue</title>'):
            with self.subTest(body=body):
                self.assertEqual(self.run_search(body=body), 'inconclusive')

    def test_status_priority(self):
        for code, status in [(401,'blocked'), (403,'blocked'), (429,'blocked'), (503,'error'), (408,'timed_out'), (404,'not_found'), (410,'not_found'), (302,'inconclusive'), (400,'inconclusive')]:
            with self.subTest(code=code):
                self.assertEqual(self.run_search(code=code), status)
        self.assertEqual(self.run_search(code=302, headers={'Location':'/login'}), 'blocked')
        self.assertEqual(self.run_search(body='<title>Just a moment...</title>'), 'blocked')
        self.assertEqual(self.run_search(body='<title>Sign in · GitHub</title>'), 'blocked')
        self.assertEqual(self.run_search(code=404, headers={'cf-mitigated':'challenge'}), 'blocked')

    def test_explicit_upstream_missing_message(self):
        self.assertEqual(self.run_search(name='1337x', body='<head><title>404 Not Found</title></head>'), 'not_found')

    def test_transport_errors(self):
        self.assertEqual(self.run_search(failure=requests.ConnectTimeout()), 'timed_out')
        self.assertEqual(self.run_search(failure=requests.ConnectionError()), 'error')

    def test_no_requests_for_invalid_platform_handle(self):
        with patch.object(adapter, 'fetch') as network:
            result = adapter.check_site('GitHub', self.sites['GitHub'], 'with_underscore', 1)
            self.assertEqual(result['status'], 'inconclusive')
            network.assert_not_called()

    def test_input_rejected_before_contact(self):
        base = {'op':'search', 'username':'blue', 'sites':['GitHub']}
        for overrides in ({'sites':['https://evil.example']}, {'sites':['GitHub', 'GitHub']}, {'sites':[]}, {'username':'../x'}, {'username':'..'}, {'timeout': True}, {'concurrency':21}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                list(adapter.events(base | overrides, self.sites))

    def test_weak_missing_markers_stay_inconclusive(self):
        for name, body in [('HackerRank','Something went wrong'), ('1337x','<title>Error something went wrong.</title>'), ('GitLab','[{"username":"blue","things":[]}]')]:
            with self.subTest(name=name):
                self.assertEqual(self.run_search(name=name, body=body), 'inconclusive')

    def test_standard_proxy_and_ca_with_anonymous_request(self):
        import os
        response = requests.Response()
        response.url = 'https://example.org/user/blue'
        response.status_code = 200
        response._content = b'profile'
        response._content_consumed = True
        with patch.dict(os.environ, {'HTTPS_PROXY':'http://proxy.invalid:8080', 'NO_PROXY':'', 'REQUESTS_CA_BUNDLE':'/org/ca.pem'}, clear=True):
            with patch.object(requests.Session, 'get', return_value=response) as get:
                adapter.fetch(response.url, 5)
        self.assertEqual(get.call_args.kwargs['proxies']['https'], 'http://proxy.invalid:8080')
        self.assertEqual(get.call_args.kwargs['verify'], '/org/ca.pem')

    def test_catalog_only_public_profile_targets(self):
        for name in ['HudsonRock', 'Steam Community (Group)', 'NationStates Region', 'Terraria Forums']:
            self.assertNotIn(name, self.sites.keys(), name)

    def test_tampered_manifest_fails_closed(self):
        import tempfile
        import catalog
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'sites.json').write_text('{}')
            with patch.object(catalog, 'DATA', Path(tmp)), self.assertRaisesRegex(ValueError, 'integrity'):
                catalog.load_sites()

    def test_challenge_wins_over_profile_markup(self):
        identity = '<meta name="octolytics-dimension-user_login" content="blue">'
        for body in ('<h1>Verify you are human</h1>', '<div class="g-recaptcha"></div>',
                     '<h1>Too many requests</h1>', '<form action="/login"><input type="password"></form>'):
            with self.subTest(challenge=body):
                self.assertEqual(self.run_search(body=identity + body), 'blocked')
