"""Require platform evidence and retain uncertainty when a probe is ambiguous."""
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit

from mainstream import mainstream_evidence
from sherlock_project.result import QueryStatus


class ProfileHead(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.canonical = ''
        self.title = ''
        self.in_title = False
        self.login_form = False
        self.gated = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = (values.get('class') or '').lower().split()
        if any(marker in classes for marker in ('g-recaptcha', 'h-captcha', 'cf-turnstile')):
            self.gated = True
        if tag == 'form':
            self.login_form = bool(GATE_PATH.search(values.get('action') or ''))
        if self.login_form and tag == 'input' and (values.get('type') or '').lower() == 'password':
            self.gated = True
        if tag == 'meta':
            key = values.get('property') or values.get('name') or ''
            self.meta[key.lower()] = values.get('content') or ''
        elif tag == 'link' and 'canonical' in (values.get('rel') or '').lower().split():
            self.canonical = values.get('href') or ''
        elif tag == 'title':
            self.in_title = True

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if data.strip().casefold() in {'verify you are human', 'too many requests', 'rate limit exceeded', 'complete the captcha to continue'}:
            self.gated = True

    def handle_endtag(self, tag):
        if tag == 'form':
            self.login_form = False
        if tag == 'title':
            self.in_title = False


def equivalent(url1, url2):
    def parts(url):
        parsed = urlsplit(url)
        return (parsed.scheme, parsed.netloc.lower().removeprefix('www.'), parsed.path.rstrip('/'), parsed.query)
    return parts(url1) == parts(url2)


GATE_TITLE = re.compile(r'^(?:sign[ -]?in|log[ -]?in|just a moment|access denied|attention required|verify (?:you are|your)|security (?:check|challenge)|authentication required|rate limit|too many requests)\b', re.I)
GATE_PATH = re.compile(r'/(?:log[_-]?in|sign[_-]?in|auth|captcha|challenge|checkpoint)(?:[/?.#]|$)', re.I)
MISSING_TITLE = re.compile(r'\b(?:404|not found|does not exist|unavailable|suspended|deactivated)\b', re.I)


def json_identity(response, username):
    try:
        data = response.json()
    except (ValueError, RecursionError):
        return False
    if isinstance(data, list):
        data = data[0] if len(data) == 1 else None
    if isinstance(data, dict) and isinstance(data.get('user'), dict):
        data = data['user']
    if not isinstance(data, dict) or not any(data.get(k) for k in ('id', 'user_id', 'uuid', 'did', 'profile_url', 'web_url')):
        return False
    handles = {username.casefold(), username.casefold() + '.bsky.social'} if urlsplit(response.url).hostname == 'public.api.bsky.app' else {username.casefold()}
    return any(isinstance(data.get(k), str) and data[k].casefold() in handles for k in ('login', 'username', 'user_name', 'handle', 'nickname'))


def classify(rule, profile, username, upstream, response):
    code = response.status_code
    location = urljoin(response.url, response.headers.get('Location', ''))
    if (upstream is QueryStatus.WAF or response.headers.get('cf-mitigated', '').lower() == 'challenge'
            or code in {401, 403, 407, 429, 451} or 300 <= code < 400 and GATE_PATH.search(urlsplit(location).path)):
        return 'blocked'
    if code in {408, 504}:
        return 'timed_out'
    if code >= 500:
        return 'error'
    media = response.headers.get('Content-Type', '').lower()
    body = response.text
    head = ProfileHead()
    if 'html' in media or body.lstrip().startswith('<'):
        try:
            head.feed(body)
        except (ValueError, AssertionError):
            return 'inconclusive'
    if head.gated or GATE_TITLE.search(head.title.strip()) or '/cdn-cgi/challenge-platform/' in body or 'challenge-error-text' in body:
        return 'blocked'
    if code in {404, 410}:
        return 'not_found'
    if rule['errorType'] == 'response_url' and 300 <= code < 400:
        error_url = rule.get('errorUrl', '').replace('{}', username)
        if error_url and equivalent(location, error_url):
            return 'not_found'
    if not 200 <= code < 300:
        return 'inconclusive'
    platform = mainstream_evidence(profile, username, response)
    if platform is not None:
        if platform[0] in {'found', 'possible'} and upstream is not QueryStatus.CLAIMED:
            return 'inconclusive'
        return platform[0]
    if upstream is QueryStatus.AVAILABLE:
        if rule['errorType'] == 'status_code':
            return 'not_found'  # e.g. an explicitly configured 204
        markers = rule.get('errorMsg', [])
        if isinstance(markers, str):
            markers = [markers]
        for marker in markers:
            if marker not in body:
                continue
            if marker in {'[]', '{"users":[]}'} and body.strip() == marker:
                return 'not_found'
            if re.search(r"not found|does(?: not|n't) exist|no such user|cannot be found|could not (?:be )?find|not a registered member|no users found", marker, re.I):
                return 'not_found'
        return 'inconclusive'
    if upstream is not QueryStatus.CLAIMED or code != 200 or not body or MISSING_TITLE.search(head.title):
        return 'inconclusive'
    if 'json' in media:
        return 'found' if json_identity(response, username) else 'inconclusive'
    github_login = head.meta.get('octolytics-dimension-user_login', '')
    if urlsplit(profile).hostname in {'github.com', 'www.github.com'} and github_login.casefold() == username.casefold():
        return 'found'
    handle = head.meta.get('profile:username', '')
    if handle and handle.casefold() != username.casefold():
        return 'inconclusive'
    if any(not equivalent(urljoin(profile, link), profile) for link in (head.canonical, head.meta.get('og:url')) if link):
        return 'inconclusive'
    identity_url = head.meta.get('og:url') or head.canonical
    if identity_url and equivalent(urljoin(profile, identity_url), profile):
        if head.meta.get('profile:username', '').casefold() == username.casefold():
            return 'found'
        if head.meta.get('og:type', '').lower() == 'profile' and re.search(r'(?<![\w.-])' + re.escape(username) + r'(?![\w.-])', head.title, re.I):
            return 'found'
        if re.match(r'^@' + re.escape(username) + r'(?:\s*[-|·]|$)', head.title.strip(), re.I):
            return 'possible'
    elif not identity_url and head.meta.get('og:type') == 'profile' and head.meta.get('profile:username', '').casefold() == username.casefold():
        return 'possible'
    return 'inconclusive'
