"""Read platform-owned metadata from public profile pages."""
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.script_id = None
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.script_id = dict(attrs).get('id', '')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.script_id = None

    def handle_data(self, data):
        if self.script_id is not None:
            self.scripts.append((self.script_id, data.strip()))


def mainstream_evidence(profile, username, response):
    host = urlsplit(profile).hostname
    if host not in {'www.youtube.com', 'www.tiktok.com'}:
        return None
    unknown = ('inconclusive', 'The public page lacked matching owner metadata.')
    if response.url.rstrip('/') != profile.rstrip('/') or response.status_code != 200:
        return unknown
    parser = Scripts()
    parser.feed(response.text)
    if host == 'www.tiktok.com' and 'Govt. of India decided to block 59 apps' in response.text:
        return 'blocked', 'Regional access restriction.'
    for tag, script in parser.scripts:
        try:
            if host == 'www.tiktok.com' and tag == '__UNIVERSAL_DATA_FOR_REHYDRATION__':
                detail = json.loads(script)['__DEFAULT_SCOPE__']['webapp.user-detail']
                if detail['statusCode'] == 10222:
                    return 'blocked', 'Private account.'
                if detail['statusCode'] == 10221:
                    return 'not_found', 'The platform reported a missing account.'
                user = detail['userInfo']['user']
                if detail['statusCode'] == 0 and user['uniqueId'].casefold() == username.casefold():
                    return ('found' if re.fullmatch(r'[1-9][0-9]*', str(user.get('id'))) else 'possible',
                            'The public profile names this handle.')
            if host == 'www.youtube.com' and script.startswith('var ytInitialData = '):
                owner = json.loads(script.removeprefix('var ytInitialData = ').removesuffix(';'))['metadata']['channelMetadataRenderer']
                urls = owner.get('ownerUrls', []) + ([owner['vanityChannelUrl']] if 'vanityChannelUrl' in owner else [])
                if urls and all(url.casefold().rstrip('/') == profile.casefold() for url in urls):
                    return ('found' if re.fullmatch(r'UC[\w-]{22}', owner.get('externalId', ''), re.ASCII) else 'possible',
                            'Channel owner metadata names this handle.')
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
            return unknown
    return unknown
