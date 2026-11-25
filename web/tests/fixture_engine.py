"""Network-free one-request child for service lifecycle tests."""
import json
import os
from pathlib import Path
import sys
import time

request = json.loads(sys.stdin.readline())
mode, path = sys.argv[1:]
Path(path).write_text(str(os.getpid()))
for site in request['sites']:
    url = {'GitHub':'https://www.github.com/', 'GitLab':'https://gitlab.com/'}[site] + request['username']
    print(json.dumps({'type':'result', 'platform':site, 'url':url if mode != 'bad' else 'https://example.org/', 'status':'possible' if mode == 'lead' else 'inconclusive'}), flush=True)
    if mode == 'block':
        time.sleep(30)
print('{"type":"done"}', flush=True)
