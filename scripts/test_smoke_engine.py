import unittest

from smoke_engine import check_closed_proxy


class ClosedProxyTest(unittest.TestCase):
    def test_classified_proxy_failure(self):
        row = dict(type="result", provider="HuntWick public lookup", platform="Lichess",
                   status="error", verdict="Proxy connection failure")
        done = {"type": "done"}
        check_closed_proxy([row, done])
        for change in ({"platform": "other"}, {"provider": "other"}, {"status": "found"},
                       {"verdict": "TLS failure"}, {"http": 200}):
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                check_closed_proxy([{**row, **change}, done])
        with self.assertRaises(RuntimeError):
            check_closed_proxy([row])
