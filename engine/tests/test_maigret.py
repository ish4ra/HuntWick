import sys
from pathlib import Path
import unittest

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapter import events, load_sites


class MaigretTests(unittest.TestCase):
    def test_provider_is_available_and_preserves_original_verdict(self):
        from unittest.mock import patch
        with patch('adapter.NetworkPool') as pool:
            response = requests.Response()
            response.status_code = 200
            response.url = 'https://api.github.com/users/fixture'
            response._content = b'{}'
            net = pool.return_value.__enter__.return_value
            net.request.return_value = response
            rows = list(events(dict(op='search', providerMode='maigret', username='fixture',
                                    sites=['GitHub']), load_sites()))
            self.assertEqual((rows[0]['provider'], rows[0]['verdict'], rows[0]['status']),
                             ('Maigret', 'Claimed', 'provider_match'))
            self.assertEqual(rows[-1], {'type': 'done'})
            self.assertEqual(net.request.call_count, 1)

    def test_deep_reconciles_evidence_and_shares_equivalent_requests(self):
        from discovery import reconcile, SharedNetwork
        from unittest.mock import Mock
        reports = [dict(provider='Maigret',verdict='Claimed',status='provider_match'),
                   dict(provider='Sherlock Original',verdict='Available',status='not_found')]
        row = reconcile(reports)
        self.assertEqual(row['status'], 'conflict')
        self.assertEqual([s['verdict'] for s in row['sources']], ['Claimed','Available'])
        network = Mock()
        response = requests.Response()
        response.url = 'https://example.org/u/demo'
        response.status_code = 200
        network.request.return_value = response
        shared = SharedNetwork(network)
        command = dict(url=response.url, method='GET', headers={}, redirect=False, origins=[response.url], timeout=2)
        self.assertIs(shared.request(command), shared.request(command))
        self.assertEqual(network.request.call_count, 1)

    def test_catalog_counts_and_policy(self):
        rows = list(events({'op':'catalog'},load_sites()))
        entries = rows[0]['sites']
        self.assertGreater(len(entries), 4000)
        self.assertEqual(len(entries),len({site['name'] for site in entries}))
        self.assertFalse(any(s['category']=='Adult (NSFW)' for s in entries))
        github = next(s for s in entries if s['name']=='GitHub')
        self.assertIn('maigret',github['engines'])
        self.assertTrue(any('maigret' in s['engines'] and 'sherlock' not in s['engines'] for s in entries))
