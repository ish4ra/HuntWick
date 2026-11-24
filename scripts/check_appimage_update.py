"""Exercise the installed Linux updater on a private HTTPS feed in a disposable checkout."""
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'x86_64-unknown-linux-gnu'
VERSION = json.loads((ROOT/'package.json').read_text())['version']


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def acceptance(tmp):
    release = tmp/'release'
    release.mkdir()
    candidate, = (ROOT/'installers'/TARGET).glob('*.AppImage')
    payload = release/'candidate.AppImage'
    shutil.copyfile(candidate, payload)
    key = tmp/'fixture.key'
    cli = ROOT/'node_modules/.bin/tauri'
    run(cli,'signer','generate','--ci','-p','','-w',key,stdout=subprocess.DEVNULL)
    env = dict(os.environ, HUNTWICK_UPDATER_PUBLIC_KEY=key.with_suffix('.key.pub').read_text().strip(),
               TAURI_SIGNING_PRIVATE_KEY=key.read_text().strip(), TAURI_SIGNING_PRIVATE_KEY_PASSWORD='')
    run(cli,'signer','sign','--app-version',VERSION,payload,env=env,stdout=subprocess.DEVNULL)
    cert, pem = tmp/'cert.pem', tmp/'server.key'
    run('openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost',
        '-addext','subjectAltName=DNS:localhost,IP:127.0.0.1','-keyout',pem,'-out',cert,stderr=subprocess.DEVNULL)

    attempts = {'/updates-preview/latest.json':0, '/updates-stable/latest.json':0}

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in attempts:
                attempts[self.path] += 1
                n = attempts[self.path]
                if self.path.startswith('/updates-stable/'):
                    if n == 1:
                        self.send_error(404)
                        return
                    data = manifest
                else:
                    data = dict(manifest)
                    if n == 1:
                        data['version'] = '0.0.1'
                    elif n == 2:
                        data['platforms'] = {'unsupported': next(iter(manifest['platforms'].values()))}
                    elif n == 3:
                        data['platforms'] = {'linux-x86_64': dict(manifest['platforms']['linux-x86_64'],signature='invalid')}
                body = json.dumps(data).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def __init__(self,*args,**kw):
            super().__init__(*args,directory=release,**kw)

    with ThreadingHTTPServer(('127.0.0.1',0),Handler) as server:
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert,pem)
        server.socket=context.wrap_socket(server.socket,server_side=True)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        origin=f'https://127.0.0.1:{server.server_port}/'
        feed=release/'updates-preview'
        feed.mkdir()
        manifest={'version':VERSION,'platforms':{'linux-x86_64':{
            'url':origin+payload.name,'signature':Path(str(payload)+'.sig').read_text().strip()}}}
        (feed/'latest.json').write_text(json.dumps(manifest))
        # Build an older installed client using exactly the candidate native updater.
        # Only its build-time trust anchor, feed, version and test driver differ.
        checkout=tmp/'old'
        run('git','clone','-q','--local',ROOT,checkout)
        (checkout/'node_modules').symlink_to(ROOT/'node_modules',target_is_directory=True)
        (checkout/'engine/dist').symlink_to(ROOT/'engine/dist',target_is_directory=True)
        service=checkout/'src-tauri/src/updates.rs'
        service.write_text(service.read_text().replace('https://github.com/ish4ra/HuntWick/releases/download/',origin))
        driver=checkout/'src/useHuntWick.ts'
        orig="void invoke('confirm_install', { siteCount })"
        assert orig in driver.read_text()
        driver.write_text(driver.read_text().replace(orig, """void (async()=>{
          const check=(prerelease:boolean)=>invoke<{version:string}|null>('check_update',{prerelease})
          const mustReject=async(p:Promise<unknown>)=>{
            try {await p} catch {return}
            throw Error('Expected update operation to fail')
          }
          await mustReject(check(false))
          if (await check(false)) throw Error('Stable check accepted a prerelease')
          if (await check(true)) throw Error('Downgrade accepted')
          await mustReject(check(true))
          const damaged=await check(true)
          if (!damaged) throw Error('Missing signature fixture')
          await mustReject(invoke('install_update',{version:damaged.version}))
          const valid=await check(true)
          if (!valid) throw Error('Missing valid update')
          await invoke('install_update',{version:valid.version})
        })().catch(console.error)"""))
        app=checkout/'src/App.tsx'
        # Avoid a background stable-feed check competing with the explicit preview check.
        app.write_text(app.read_text().replace('ws.desktop && <Updates','ws.desktop && !("__HUNTWICK_VERIFY_INSTALL__" in window) && <Updates'))
        env.update(CARGO_TARGET_DIR=str(ROOT/'src-tauri/target'), APPIMAGE_EXTRACT_AND_RUN='1')
        run(cli,'build','--ci','--target',TARGET,'--bundles','appimage','--config',
            json.dumps({'version':'0.1.0-rc.1'}),'--','--locked',cwd=checkout,env=env)
        old,=(ROOT/'src-tauri/target'/TARGET/'release/bundle/appimage').glob('*0.1.0-rc.1*.AppImage')
        installed=tmp/'installed.AppImage'
        shutil.copy2(old,installed)
        with payload.open('rb') as stream:
            expected=hashlib.file_digest(stream,'sha256').digest()
        env.update(SSL_CERT_FILE=str(cert),NO_PROXY='localhost,127.0.0.1',no_proxy='localhost,127.0.0.1',
                   XDG_CONFIG_HOME=str(tmp/'prefs'),XDG_DATA_HOME=str(tmp/'data'),XDG_CACHE_HOME=str(tmp/'cache'))
        p=subprocess.Popen([installed,'--verify-install'],env=env)
        try:
            end=time.monotonic()+120
            while time.monotonic()<end:
                if installed.stat().st_size==payload.stat().st_size:
                    with installed.open('rb') as f:
                        if hashlib.file_digest(f,'sha256').digest()==expected:break
                time.sleep(.5)
            else:
                raise RuntimeError(f'Image replacement failed after feed requests {attempts}, client exit {p.poll()}.')
            if list(attempts.values()) != [4,2]:
                raise RuntimeError('Unexpected update feed request sequence.')
            run(installed,'--verify-install',env=env,timeout=90)
        finally:
            if p.poll() is None:p.terminate()
            p.wait(timeout=20)
            server.shutdown()


if __name__=='__main__':
    with tempfile.TemporaryDirectory() as tmp:
        try:
            acceptance(Path(tmp))
        except (RuntimeError, subprocess.SubprocessError) as exc:
            print(f'::error title=AppImage upgrade fixture::{exc}', flush=True)
            raise
    print('Verified in-place Linux AppImage update and startup of the replaced image.')
