"""Compare the installed Sherlock CLI and HuntWick on identical offline pages."""
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import requests

ENGINE = Path(__file__).resolve().parents[1]
HANDLE = 'fixture-account'
TITLE = '<title>@fixture-account | Example</title>'
PROFILE = '<meta property="og:type" content="profile">'
META = '<meta property="profile:username" content="fixture-account">'
CANONICAL = '<link rel="canonical" href="{url}">'
# name -> HTTP status, document, upstream CSV result, adapter state
CASES = {
    'Verified': (200, CANONICAL + META, 'Claimed', 'found'),
    'PossiblyHTML': (200, TITLE + CANONICAL, 'Claimed', 'possible'),
    'PossiblyMetadata': (200, PROFILE + META, 'Claimed', 'possible'),
    'Generic': (200, '<title>Welcome</title>', 'Claimed', 'inconclusive'),
    'Echo': (200, TITLE, 'Claimed', 'inconclusive'),
    'SearchPage': (200, '<title>Search results for @fixture-account</title>' + CANONICAL, 'Claimed', 'inconclusive'),
    'WrongURL': (200, PROFILE + META + '<link rel="canonical" href="https://other.invalid/">', 'Claimed','inconclusive'),
    'Missing': (404, '<title>Not Found</title>', 'Available','not_found'),
    'MissingMessage': (200, 'User not found', 'Available','not_found'),
    'RateLimit': (429, META + PROFILE, 'Available','blocked'),
    'Challenge': (200, '<title>Just a moment...</title>' + PROFILE + META, 'Claimed','blocked'),
    'Login': (200, '<title>Log in</title>' + PROFILE + META, 'Claimed','blocked'),
    'Failure': (503, PROFILE + META, 'Available','error'),
}


def rules():
    base = {'username_claimed': HANDLE, 'urlMain':'https://example.invalid/', 'request_method':'GET', 'errorType':'status_code'}
    manifest = {k: base | {'url':f'https://example.invalid/{k}/{{}}'} for k in CASES}
    manifest['MissingMessage'].update(errorType='message', errorMsg='User not found')
    return manifest


def reply(url):
    response = requests.Response()
    response.url = url
    response.encoding = 'utf-8'
    if url.startswith('https://api.github.com/repos/sherlock-project/sherlock/'):
        code, body = 200, '{"tag_name":"v0.16.2"}'
    else:
        code, body, _, _ = CASES[url.split('/')[-2]]
    response.status_code = code
    response._content = body.replace('{url}',url).encode()
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


def run_cli():
    # Exercise the official argument parser, loader, classifier and CSV writer in
    # a fresh interpreter. Only replace the network, including the update check.
    from sherlock_project.sherlock import main
    with tempfile.TemporaryDirectory() as directory:
        manifest = Path(directory) / 'sites.json'
        manifest.write_text(json.dumps(rules()))
        args = ['sherlock', HANDLE, '--json', str(manifest), '--ignore-exclusions', '--no-color', '--folderoutput', directory, '--csv', '--print-all']
        with (patch.object(sys,'argv',args), patch.object(requests.Session, 'request', lambda self,method,url,**kw:reply(url)), redirect_stdout(io.StringIO())):
            main()
        with (Path(directory)/f'{HANDLE}.csv').open() as report:
            return {row['name']:row['exists'] for row in csv.DictReader(report)}


class ParityTests(unittest.TestCase):
    def test_official_cli_and_adapter_classifications(self):
        sys.path.insert(0, str(ENGINE))
        import adapter
        cli = subprocess.run([sys.executable, __file__, '--upstream'], check=True, capture_output=True, text=True, timeout=20)
        official = json.loads(cli.stdout)
        with patch.object(adapter, 'fetch', lambda url,timeout:reply(url)):
            for name, rule in rules().items():
                with self.subTest(name=name):
                    self.assertEqual(official[name], CASES[name][2])
                    self.assertEqual(adapter.check_site(name, rule, HANDLE, 1)['status'], CASES[name][3])


if __name__ == '__main__' and '--upstream' in sys.argv:
    print(json.dumps(run_cli()))
