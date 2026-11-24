import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import load_sites, describe, UNSUPPORTED_PROBES


class PolicyTests(unittest.TestCase):
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
