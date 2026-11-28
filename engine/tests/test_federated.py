import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
import requests

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import load_sites
from discovery import directory, run_profile


class LocalIdentity(unittest.TestCase):
    items = directory(load_sites(),False,False)

    def outcome(self, instance, data, code=200, media='application/json', failure=None):
        net = Mock()
        res = Mock(text='',status_code=code, headers={'Content-Type':media}, url='https://'+instance)
        res.json.return_value = data
        net.request.return_value = res
        net.request.side_effect = failure
        row = run_profile('maigret',instance,self.items[instance],'fixture',3,net,False)
        self.assertFalse(net.request.call_args.args[0]['redirect'])
        return row['status']

    def test_mastodon_instances(self):
        for host in ('mastodon.social','mastodon.online'):
            local = dict(id='12',username='Fixture',acct='fixture',url=f'https://{host}/@fixture')
            self.assertEqual(self.outcome(host,local),'found')
            for override in [dict(acct='fixture@other.example'),dict(username='other'),dict(url='https://other.example/@fixture')]:
                self.assertEqual(self.outcome(host,local|override),'inconclusive')
            for code,data,media,expected in [(200,{},'text/html','inconclusive'),(302,{},'text/html','inconclusive'),
                    (404,{'error':'Record not found'},'application/json','not_found'),(404,{},'text/html','inconclusive'),
                    (429,{},'application/json','blocked')]:
                self.assertEqual(self.outcome(host,data,code,media),expected)
            for failure,status in [(requests.Timeout(),'timed_out'),(requests.ConnectionError(),'error')]:
                self.assertEqual(self.outcome(host,None,failure=failure),status)

    def test_lemmy_local_actor(self):
        person = dict(id=9,name='fixture',local=True,actor_id='https://lemmy.ml/u/fixture')
        for change,expected in [({},'found'),({'local':False},'inconclusive'),({'name':'someone'},'inconclusive'),
                                ({'actor_id':'https://elsewhere.example/u/fixture'},'inconclusive')]:
            self.assertEqual(self.outcome('lemmy.ml',{'person_view':{'person':person|change}}),expected)
