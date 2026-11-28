import unittest
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import load_sites, describe, UNSUPPORTED_PROBES


class PolicyTests(unittest.TestCase):
    def test_deep_search_and_catalog_agree_on_each_policy_combination(self):
        from adapter import events
        from maigret_provider import eligible

        names = ['Ordinary fixture', 'Adult fixture', 'Excluded fixture', 'Both fixture']
        entries = {}
        for index, name in enumerate(names):
            root = f'https://site{index}.invalid'
            entries[name] = {'category':'Forums', 'rule':{'url':root + '/u/{username}', 'urlMain':root}}
        entries['Adult fixture']['category'] = 'Adult (NSFW)'
        snapshot = {'entries':entries, 'unavailable':{}}
        # The second restricted fixture inherits its adult flag from Sherlock by name.
        with TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / 'sites.json').write_text(json.dumps({'Both fixture':{'isNSFW':True}}))
            (data / 'exclusions.txt').write_text('Excluded fixture\nBoth fixture\n')
            eligible.cache_clear()
            self.addCleanup(eligible.cache_clear)
            with (patch('maigret_provider.DATA', data),
                  patch('maigret_provider.snapshot', return_value=snapshot),
                  patch('discovery.snapshot', return_value=snapshot),
                  patch('discovery.check', return_value={'provider':'Maigret','status':'inconclusive'}) as check):
                for adult, experimental, expected in (
                    (False, False, [names[0]]), (True, False, names[:2]),
                    (False, True, [names[0], names[2]]), (True, True, names)
                ):
                    policy = dict(includeNsfw=adult, includeExcluded=experimental)
                    catalog = next(events(dict(op='catalog', **policy), {}))
                    visible = {entry['name'] for entry in catalog['sites'] if entry['name'] in names}
                    self.assertEqual(visible, set(expected))
                    request = dict(op='search', providerMode='deep', username='fixture', **policy)
                    for name in names:
                        with self.subTest(adult=adult, experimental=experimental, platform=name):
                            check.reset_mock()
                            if name in expected:
                                row, done = events(dict(request, sites=[name]), {})
                                self.assertEqual((row['platform'], done['type']), (name, 'done'))
                                check.assert_called_once()
                            else:
                                with self.assertRaisesRegex(ValueError, 'bundled catalog'):
                                    list(events(dict(request, sites=[name]), {}))
                                check.assert_not_called()

    def test_policies_are_independent(self):
        base, adult, experimental, both = [load_sites(*x) for x in [(False, False), (True, False), (False, True), (True, True)]]
        self.assertLess(base.keys(), adult.keys())
        self.assertLess(base.keys(), experimental.keys())
        self.assertIn('Reddit', experimental)
        self.assertNotIn('Reddit', adult)
        self.assertFalse(UNSUPPORTED_PROBES.intersection(both))
        for name in adult.keys() - base.keys():
            self.assertTrue(adult[name]['isNSFW'])
        self.assertFalse(any(s.get('isNSFW') for s in experimental.values()))
        directory = describe(both, 'fixture')
        self.assertNotIn('Reddit', [s['name'] for s in directory['unavailable']])
        self.assertIn('Adult (NSFW)', [s['category'] for s in directory['sites']])
        with self.assertRaises(ValueError):
            load_sites('false')
