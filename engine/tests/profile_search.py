"""Historical bounded-GET transport fixture profile. Usage: python profile_search.py ENGINE_DIR."""
import json
import os
from pathlib import Path
from statistics import median
import subprocess
import sys
from time import monotonic, sleep


def fixture_child(engine, mode):
    sys.path.insert(0, str(engine))
    import adapter
    import requests

    sites = adapter.load_sites()
    catalog = adapter.describe(sites, adapter.__version__)
    names = [s['name'] for s in catalog['sites'] if mode == 'full' or s['quick']]
    if mode == 'cancel':
        names = ['GitHub']

    def fetch(url, timeout):
        if mode == 'cancel':
            print('ready', flush=True)
            sleep(30)
        sleep(.008)
        r = requests.Response()
        r.url = url
        r.encoding = 'utf-8'
        r.status_code = 200
        r.headers['Content-Type'] = 'text/html; charset=utf-8'
        r._content = b'<html><title>Welcome</title><p>' + b'x' * 16384 + b'</p></html>'
        return r

    adapter.fetch = fetch
    if mode == 'cancel':
        raise SystemExit(adapter.main())
    for frame in adapter.events({'op':'search','providerMode':'hosted','username':'fixture123','sites':names,'timeout':3,'concurrency':8},sites):
        print(frame['type'], flush=True)


def sample(engine, mode):
    command = [sys.executable, __file__, str(engine), '--child', mode]
    if mode == 'catalog':
        command = [sys.executable, str(engine/'adapter.py')]
    env = {**os.environ, 'OPENBLAS_NUM_THREADS':'1', 'PYTHONHASHSEED':'0'}
    start = monotonic()
    if mode == 'cancel':
        env['HUNTWICK_PARENT_PIPE'] = '1'
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,env=env)
    try:
        if mode == 'catalog':
            p.stdin.write('{"op":"catalog"}\n'); p.stdin.flush()
        if mode == 'cancel':
            p.stdin.write('{"op":"search","providerMode":"hosted","username":"fixture123","sites":["GitHub"]}\n'); p.stdin.flush()
        first = p.stdout.readline()
        if not first:
            raise RuntimeError('Fixture engine exited early')
        first_ms = (monotonic()-start)*1000
        cancel_start = monotonic()
        p.stdin.close()
        remaining = p.stdout.readlines()
        code = p.wait(timeout=10)
        if mode == 'cancel':
            assert first.strip() == 'ready' and code != 0
            return first_ms, (monotonic()-cancel_start)*1000, 1
        assert code == 0
        return first_ms, (monotonic()-start)*1000, len(remaining)
    finally:
        p.kill(); p.wait()


if __name__ == '__main__':
    engine = Path(sys.argv[1]).resolve()
    if '--child' in sys.argv:
        fixture_child(engine, sys.argv[-1])
    else:
        for mode in ('catalog','quick','full','cancel'):
            samples = [sample(engine,mode) for _ in range(5)]
            print(mode, [round(median(column),1) for column in zip(*samples)], flush=True)
