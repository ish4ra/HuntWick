"""Read only the bundled, integrity-checked Sherlock definitions."""
from hashlib import sha256
from pathlib import Path
import re
from urllib.parse import urlsplit

from sherlock_project.sites import SitesInformation

DATA = Path(__file__).parent / 'data'
DATABASE_VERSION = '4e2a4f6 + exclusions 7ce4f61'
UPDATED_AT = '2026-05-04'  # Last upstream change to sites.json; see notices/Provenance.md.
DIGESTS = {
    'sites.json': '3fdfc6694c5cd99798881215554b09e617c6d5284a6219fae309882566a9fb30',
    'exclusions.txt': '532677e9de8c4c495e9b89062fc6fc44f4f96846919b5dac03efcab808616daa',
}

QUICK = {'GitHub', 'GitLab', 'Docker Hub', 'Codeberg', 'Hugging Face', 'DEV Community', 'Lichess', 'Bluesky', 'Trello', 'Codewars', 'Wattpad', 'ArtStation'}
GROUPS = {
    'Development': {'GitHub', 'GitLab', 'Gitea', 'Gitee', 'Codeberg', 'PyPi', 'npm', 'Codepen', 'DEV Community', 'CodeSandbox', 'Docker Hub', 'Codewars', 'Hugging Face', 'RubyGems', 'Packagist', 'SourceForge', 'Codecademy', 'freecodecamp'},
    'Social Media': {'Bluesky', 'mastodon.social', 'mstdn.social', 'Fosstodon', 'Clubhouse', 'VK', 'Telegram', 'Snapchat', 'TikTok', 'threads', 'Pinterest', 'tumblr', 'SpaceHey', 'YouTube'},
    'Gaming': {'Lichess', 'Chess', 'Itch.io', 'Xbox Gamertag', 'PSNProfiles.com', 'Twitch', 'Steam Community (User)', 'Speedrun.com', 'Roblox', 'osu!', 'TETR.IO'},
    'Creative': {'ArtStation', 'Behance', 'Dribbble', 'Wattpad', 'SoundCloud', 'Flickr', 'Unsplash', 'Vimeo', 'Sketchfab', 'Bandcamp', 'Medium', 'Substack', 'WordPress', 'SpeakerDeck'},
    'Forums': {'Discuss.Elastic.co', 'Caddy Community', 'Joplin Forum', 'Cryptomator Forum', 'Python.org Discussions', 'n8n Community', 'Jupyter Community Forum', 'SublimeForum', 'CloudflareCommunity', 'Chaos', 'GameFAQs', 'Disqus', 'Lobsters'},
    'Entertainment': {'TheMovieDB', 'MyAnimeList', 'Letterboxd', 'Discogs', 'Rumble', 'MixCloud', 'last.fm', 'Smule', 'MyDramalist', 'Sporcle'},
    'Professional': {'LinkedIn', 'Trello', 'Freelancer', 'Kaggle', 'ResearchGate', 'Credly', 'Patreon', 'ProductHunt', 'Open Collective'},
}

# Upstream includes a few third-party mirrors and account-registration checks.
# These cannot establish that a public profile exists on the selected service.
UNSUPPORTED_PROBES = {'Instagram', 'Twitter', 'Venmo', 'BoardGameGeek', 'minds', 'omg.lol', 'Slack',
                      'HudsonRock', 'Steam Community (Group)', 'NationStates Region', 'Terraria Forums', 'Chess'}


def valid_https(url):
    parsed = urlsplit(url.replace('{}', 'sample'))
    return (parsed.scheme == 'https' and parsed.hostname and '.' in parsed.hostname
            and not parsed.username and not parsed.password and parsed.port is None
            and not parsed.fragment and not any(c.isspace() for c in url))


def load_sites():
    for filename, expected in DIGESTS.items():
        if sha256((DATA / filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Bundled Sherlock database integrity check failed.')
    excluded = set((DATA / 'exclusions.txt').read_text('utf-8').splitlines()) | UNSUPPORTED_PROBES
    manifest = SitesInformation(str(DATA / 'sites.json'), honor_exclusions=False)
    manifest.remove_nsfw_sites()
    sites = {}
    for site in manifest:
        rule = site.information
        profile = rule['url']
        probe = rule.get('urlProbe', profile)
        if (site.name in excluded or rule.get('request_method', 'GET') not in {'GET', 'HEAD'}
                or rule.get('request_payload') or profile.count('{}') != 1 or probe.count('{}') != 1
                or not all(valid_https(url) for url in (profile, probe, rule['urlMain']))):
            continue
        if rule['errorType'] not in {'message', 'response_url', 'status_code'}:
            raise ValueError('Unsupported rule in bundled database.')
        if 'regexCheck' in rule:
            re.compile(rule['regexCheck'])
        sites[site.name] = rule
    return sites


def describe(sites, version):
    entries = []
    for name in sorted(sites, key=str.casefold):
        default = 'Forums' if 'forum' in name.casefold() else 'Other'
        category = next((group for group, names in GROUPS.items() if name in names), default)
        entries.append({'name': name, 'url': sites[name]['urlMain'], 'category': category, 'quick': name in QUICK})
    return {'type': 'catalog', 'version': version, 'updatedAt': UPDATED_AT,
            'databaseVersion': DATABASE_VERSION, 'sites': entries}
