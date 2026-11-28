import json
import sys
import unittest
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from catalog import describe, load_sites
from mainstream import mainstream_evidence


def tiktok_script(detail):
    payload = {'__DEFAULT_SCOPE__': {'webapp.user-detail': detail}}
    return '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">' + json.dumps(payload) + '</script>'


def youtube_script(metadata):
    data = {'metadata': {'channelMetadataRenderer': metadata}}
    return '<script>var ytInitialData = ' + json.dumps(data) + ';</script>'


class MainstreamTests(unittest.TestCase):
    handle = 'fixture-user'
    channel = 'UC' + 'a' * 22

    def result(self, domain, html, landed=None):
        profile = f'https://www.{domain}/@{self.handle}'
        response = requests.Response()
        response.status_code = 200
        response.url = landed or profile
        response._content = html.encode()
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        status, message = mainstream_evidence(profile, self.handle, response)
        self.assertTrue(message)
        return status

    def test_catalog_separates_unsupported_platforms_from_search_targets(self):
        sites = load_sites()
        catalog = describe(sites, 'fixture')
        unavailable = {entry['name']: entry['reason'] for entry in catalog['unavailable']}
        for site in ['Instagram', 'X (Twitter)', 'Reddit', 'Facebook']:
            self.assertTrue(unavailable[site])
            self.assertNotIn(site, sites)
        self.assertNotIn('Twitter', sites)
        for name in ['YouTube', 'TikTok']:
            self.assertIn(name, sites)
            self.assertNotIn(name, unavailable)
            self.assertNotIn('urlProbe', sites[name])

    def test_youtube_binds_channel_id_to_its_own_handle(self):
        owner = 'https://www.youtube.com/@Fixture-User'
        metadata = {'externalId': self.channel, 'vanityChannelUrl': owner}
        self.assertEqual(self.result('youtube.com', youtube_script(metadata)), 'found')
        self.assertEqual(self.result('youtube.com', youtube_script({'ownerUrls':[owner]})), 'possible')
        for other in ['https://other.example/@fixture-user', 'https://www.youtube.com/@other']:
            self.assertEqual(self.result('youtube.com', youtube_script(dict(metadata, vanityChannelUrl=other))), 'inconclusive')

    def test_tiktok_binds_user_id_and_handle_in_owner_object(self):
        detail = {'statusCode':0, 'userInfo':{'user':{'id':'12345','uniqueId':'Fixture-User'}}}
        self.assertEqual(self.result('tiktok.com', tiktok_script(detail)), 'found')
        del detail['userInfo']['user']['id']
        self.assertEqual(self.result('tiktok.com', tiktok_script(detail)), 'possible')
        detail['userInfo']['user']['uniqueId'] = 'fixture-user-other'
        self.assertEqual(self.result('tiktok.com', tiktok_script(detail)), 'inconclusive')

    def test_private_regional_and_missing_tiktok_responses(self):
        for code, status in [(10222,'blocked'), (10221,'not_found'), (777,'inconclusive')]:
            self.assertEqual(self.result('tiktok.com', tiktok_script({'statusCode':code})), status)
        self.assertEqual(self.result('tiktok.com', 'Govt. of India decided to block 59 apps'), 'blocked')
        self.assertEqual(self.result('tiktok.com', '<div>"statusCode":10221</div>'), 'inconclusive')

    def test_generic_reflections_unrelated_channels_and_malformed_html(self):
        for host in ['tiktok.com','youtube.com']:
            for html in ['fixture-user', '<meta property="og:type" content="profile"><link rel="canonical" href="/@fixture-user">',
                         '<script>var ytInitialData = {"incomplete":</script>']:
                self.assertEqual(self.result(host, html), 'inconclusive')
        unrelated = {'videoDetails':{'ownerUrls':['https://www.youtube.com/@fixture-user'], 'externalId':self.channel}}
        self.assertEqual(self.result('youtube.com', '<script>var ytInitialData = '+json.dumps(unrelated)+';</script>'), 'inconclusive')
