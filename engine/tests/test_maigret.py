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
