"""Single-worker, authenticated HuntWick web edition."""
import asyncio
import base64
import binascii
from collections import deque
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
from time import monotonic

from fastapi import FastAPI, HTTPException, Request
from sherlock_project import __version__ as sherlock_version
from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import ClientDisconnect
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.staticfiles import StaticFiles

from engine.catalog import describe, load_sites

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMMAND = (sys.executable, '-E', '-B', str(ROOT / 'engine' / 'adapter.py'))
# Pin complete upstream routes, including the separate GitLab probe. Revalidate
# on each service startup so changing a desktop rule cannot expand web egress.
ROUTES = {
    'GitHub': ('https://www.github.com/{}', 'https://www.github.com/{}'),
    'GitLab': ('https://gitlab.com/{}', 'https://gitlab.com/api/v4/users?username={}'),
}
STATUSES = {'found', 'possible', 'not_found', 'inconclusive', 'timed_out', 'blocked', 'cancelled', 'error'}
RUN_ID = re.compile(r'[a-zA-Z0-9_-]{1,96}')
HANDLE = re.compile(r'[a-zA-Z0-9_.-]{1,64}')
COOKIE = 'huntwick_session'
CSP = "default-src 'self'; connect-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"


def hosted_catalog():
    database = load_sites()
    selected = {}
    for name, routes in ROUTES.items():
        rule = database[name]
        if (rule['url'], rule.get('urlProbe', rule['url'])) != routes or rule.get('request_method', 'GET') != 'GET':
            raise RuntimeError('Hosted Sherlock rules require review.')
        selected[name] = rule
    catalog = describe(selected, sherlock_version)
    catalog.pop('unavailable', None)  # The hosted directory exposes only approved routes.
    return catalog


class Guard:
    """Authenticate before FastAPI reads a body or serves a static file."""
    def __init__(self, app, password, public_origin):
        self.app = app
        self.credential = ('huntwick:' + password).encode() if password else None
        self.public_origin = public_origin.rstrip('/') if public_origin else None
        self.key = secrets.token_bytes(32)

    def signature(self, value):
        return hmac.digest(self.key, value.encode(), 'sha256').hex()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        origin = self.public_origin or (scope['scheme'] + '://' + headers.get('host', ''))
        cookie = None

        async def secure_send(event):
            if event['type'] == 'http.response.start':
                output = MutableHeaders(scope=event)
                for key, value in [('Cache-Control','no-store'), ('Referrer-Policy','no-referrer'),
                                   ('X-Content-Type-Options','nosniff'), ('Content-Security-Policy',CSP),
                                   ('X-Frame-Options','DENY')]:
                    output[key] = value
                if cookie:
                    output.append('Set-Cookie', cookie)
            await send(event)

        async def deny(status, message, response_headers=None):
            await JSONResponse({'detail':message}, status_code=status, headers=response_headers)(scope, receive, secure_send)

        if not self.credential:
            return await deny(503, 'Hosted access is not configured.')
        if scope['path'] == '/healthz' and scope['method'] in {'GET','HEAD'}:
            return await self.app(scope, receive, secure_send)
        scheme, _, encoded = headers.get('authorization','').partition(' ')
        try:
            raw = base64.b64decode(encoded, validate=True) if scheme.lower() == 'basic' and len(encoded) <= 4096 else b''
        except (ValueError, binascii.Error):
            raw = b''
        if not hmac.compare_digest(self.credential, raw):
            return await deny(401, 'Sign in to HuntWick.', {'WWW-Authenticate':'Basic realm="HuntWick", charset="UTF-8"'})
        if scope['method'] == 'POST':
            if (headers.get('origin', origin) != origin or
                    headers.get('sec-fetch-site', 'same-origin') not in {'same-origin', 'none'}):
                return await deny(403, 'Same-origin requests are required.')
            if headers.get('content-type','').partition(';')[0].strip().lower() != 'application/json':
                return await deny(415, 'Send an application/json request.')
        owner = Request(scope).cookies.get(COOKIE, '')
        nonce, _, signature = owner.partition('.')
        if not re.fullmatch(r'[0-9a-f]{32}', nonce) or not hmac.compare_digest(self.signature(nonce).encode(), signature.encode()):
            nonce = secrets.token_hex(16)
            owner = nonce + '.' + self.signature(nonce)
            cookie = f'{COOKIE}={owner}; Path=/; HttpOnly; SameSite=Strict'
            if origin.startswith('https://'):
                cookie += '; Secure'
        state = scope.setdefault('state', {})
        state['owner'] = owner
        peer = scope.get('client')
        state['peer'] = self.signature(peer[0] if peer else 'local')
        await self.app(scope, receive, secure_send)


async def read_payload(request, allow_empty=False):
    data = bytearray()
    try:
        async for chunk in request.stream():
            if len(chunk) > 4096 - len(data):
                raise HTTPException(413, 'Request body is too large.')
            data.extend(chunk)
        if not data and allow_empty:
            return {}
        payload = json.loads(data)
    except (ValueError, RecursionError, ClientDisconnect):
        raise HTTPException(400, 'Invalid JSON request.') from None
    if not isinstance(payload, dict):
        raise HTTPException(400, 'Expected one JSON object.')
    return payload


def validate(payload):
    if set(payload) != {'id','username','sites','timeout','concurrency'}:
        raise HTTPException(400, 'Invalid search fields.')
    run_id, username, sites = payload['id'], payload['username'], payload['sites']
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise HTTPException(400, 'Invalid search ID.')
    if not isinstance(username, str) or not HANDLE.fullmatch(username) or username in {'.', '..'}:
        raise HTTPException(400, 'Enter one valid username.')
    if (not isinstance(sites, list) or not 1 <= len(sites) <= len(ROUTES)
            or any(not isinstance(s, str) or s not in ROUTES for s in sites) or len(set(sites)) != len(sites)):
        raise HTTPException(400, 'Select unique platforms from the hosted catalog.')
    for key, upper in [('timeout',20), ('concurrency',2)]:
        if type(payload[key]) is not int or not 1 <= payload[key] <= upper:
            raise HTTPException(400, f'{key} must be between 1 and {upper}.')


@dataclass(frozen=True)
class Limits:
    active_global: int = 2
    searches_per_client: int = 6
    searches_global: int = 24
    window: int = 600
    clients: int = 256
    deadline: int = 45


class Jobs:
    def __init__(self, limits, command):
        self.limits = limits
        self.command = command
        self.active = {}
        self.clients = {}
        self.recent = deque()

    def start(self, payload, peer, owner):
        cutoff = monotonic() - self.limits.window
        for times in [self.recent, *self.clients.values()]:
            while times and times[0] <= cutoff:
                times.popleft()
        self.clients = {key: times for key, times in self.clients.items() if times}
        if payload['id'] in self.active:
            raise HTTPException(409, 'A search with this ID is active.')
        times = self.clients.get(peer, deque())
        if (len(self.active) >= self.limits.active_global or any(job.peer == peer for job in self.active.values())
                or len(times) >= self.limits.searches_per_client or len(self.recent) >= self.limits.searches_global
                or (peer not in self.clients and len(self.clients) >= self.limits.clients)):
            raise HTTPException(429, 'Hosted search limit reached. Try again later.')
        now = monotonic()
        times.append(now)
        self.recent.append(now)
        self.clients[peer] = times
        job = Job(self, payload, peer, owner)
        self.active[job.id] = job
        job.task = asyncio.create_task(job.run())
        return job


class Job:
    def __init__(self, jobs, payload, peer, owner):
        self.jobs, self.id, self.peer, self.owner = jobs, payload['id'], peer, owner
        self.request = {k:v for k,v in payload.items() if k != 'id'} | {'op':'search', 'providerMode':'hosted'}
        self.pending = dict.fromkeys(payload['sites'])
        self.stop = asyncio.Event()
        self.frames = asyncio.Queue(maxsize=len(self.pending) + 1)
        self.task = None

    def report(self, name, status):
        url = ROUTES[name][0].format(self.request['username'])
        self.frames.put_nowait({'id':self.id, 'type':'result','platform':name,'url':url,'status':status})
        del self.pending[name]

    async def read_engine(self, process):
        process.stdin.write(json.dumps(self.request).encode() + b'\n')
        await process.stdin.drain()
        while line := await process.stdout.readline():
            frame = json.loads(line)
            if not isinstance(frame, dict):
                break
            if frame.get('type') == 'done':
                if self.pending or await process.stdout.read(1) or await process.wait() != 0:
                    break
                return
            name, status = frame.get('platform'), frame.get('status')
            if (frame.get('type') != 'result' or name not in self.pending or status not in STATUSES
                    or frame.get('url') != ROUTES[name][0].format(self.request['username'])):
                break
            self.report(name, status)
        raise ValueError('Invalid engine output.')

    async def run(self):
        process = None
        waits = []
        terminal = {'id':self.id, 'type':'done'}
        # Keep the web password, hosting tokens and user credentials out of the child.
        keep = {'PATH','SYSTEMROOT','WINDIR','TMP','TEMP','TMPDIR','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY',
                'REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE','SSL_CERT_FILE','SSL_CERT_DIR','LANG','LC_ALL','LD_LIBRARY_PATH'}
        env = {k:v for k,v in os.environ.items() if k.upper() in keep}
        env.update(HUNTWICK_PARENT_PIPE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
        start = monotonic()
        try:
            process = await asyncio.create_subprocess_exec(*self.jobs.command, stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, limit=4096, env=env)
            reader = asyncio.create_task(self.read_engine(process))
            stopped = asyncio.create_task(self.stop.wait())
            waits = [reader, stopped]
            await asyncio.wait(waits, timeout=max(0, self.jobs.limits.deadline - (monotonic() - start)),
                               return_when=asyncio.FIRST_COMPLETED)
            if reader.done():
                reader.result()
            else:
                for name in list(self.pending):
                    self.report(name, 'cancelled' if self.stop.is_set() else 'timed_out')
        except (OSError, ValueError, TypeError, RecursionError):
            terminal = {'id':self.id,'type':'error','message':'The hosted engine could not complete this search.'}
        finally:
            for task in waits:
                task.cancel()
            if process is not None:
                if process.returncode is None:
                    with suppress(ProcessLookupError):
                        process.kill()
                process.stdin.close()
                await asyncio.gather(*waits, return_exceptions=True)
                # Drain bounded pipe buffers after a malformed producer has been
                # killed, so wait() also reaps a producer paused by flow control.
                while await process.stdout.read(8192):
                    pass
                await process.wait()
            self.jobs.active.pop(self.id, None)
            self.frames.put_nowait(terminal)


class RunStream(Response):
    media_type = 'application/x-ndjson'

    def __init__(self, job):
        super().__init__(headers={'X-Accel-Buffering':'no'})
        del self.headers['content-length']
        self.job = job

    async def __call__(self, scope, receive, send):
        async def stream():
            await send({'type':'http.response.start','status':200,'headers':self.raw_headers})
            while True:
                frame = await self.job.frames.get()
                more = frame['type'] == 'result'
                await send({'type':'http.response.body','body':json.dumps(frame).encode() + b'\n','more_body':more})
                if not more:
                    return

        async def disconnect():
            while (await receive())['type'] != 'http.disconnect':
                pass

        writer, listener = asyncio.create_task(stream()), asyncio.create_task(disconnect())
        try:
            await asyncio.wait([writer, listener],return_when=asyncio.FIRST_COMPLETED)
            if writer.done():
                with suppress(OSError):
                    writer.result()
        finally:
            self.job.stop.set()
            writer.cancel()
            listener.cancel()
            await asyncio.gather(writer, listener, return_exceptions=True)
            await asyncio.shield(self.job.task)


def create_app(*, password=None, public_origin=None, limits=None, command=DEFAULT_COMMAND, static=ROOT/'dist'):
    jobs = Jobs(limits or Limits(), command)
    catalog = hosted_catalog()

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            active = list(jobs.active.values())
            for job in active:
                job.stop.set()
            await asyncio.gather(*(job.task for job in active))

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.jobs = jobs
    app.add_middleware(Guard, password=password, public_origin=public_origin)

    @app.get('/healthz')
    async def health():
        return {'status':'ok'}

    @app.get('/api/catalog')
    async def get_catalog():
        return catalog

    @app.post('/api/search')
    async def search(request: Request):
        payload = await read_payload(request)
        validate(payload)
        return RunStream(jobs.start(payload, request.state.peer, request.state.owner))

    @app.post('/api/search/{run_id}/cancel')
    async def cancel(run_id: str, request: Request):
        if await read_payload(request, allow_empty=True):
            raise HTTPException(400, 'Invalid cancellation request.')
        job = jobs.active.get(run_id)
        if job is None or not hmac.compare_digest(job.owner, request.state.owner):
            raise HTTPException(404, 'Search is not active.')
        job.stop.set()
        await asyncio.shield(job.task)
        return Response(status_code=204)

    @app.get('/')
    async def index():
        return FileResponse(static / 'index.html')

    @app.get('/{asset}')
    async def icon(asset: str):
        if asset not in {'huntwick.svg','huntwick-wordmark.svg','huntwick-wordmark-light.svg','huntwick-preview.png'}:
            raise HTTPException(404, 'Not found.')
        return FileResponse(static / asset)

    app.mount('/platforms', StaticFiles(directory=static / 'platforms',check_dir=False))
    app.mount('/assets', StaticFiles(directory=static / 'assets',check_dir=False))
    return app


app = create_app(password=os.getenv('HUNTWICK_WEB_PASSWORD'),
                 public_origin=os.getenv('HUNTWICK_PUBLIC_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL'))
