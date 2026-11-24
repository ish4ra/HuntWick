"""Exercise the installed Linux updater on a private HTTPS feed in a disposable checkout."""
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import ssl
import subprocess
import tempfile
import threading
import time

from smoke_desktop import desktop_environment

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
    ca, ca_key = tmp/'root.pem', tmp/'root.key'
    cert, pem, csr = tmp/'cert.pem', tmp/'server.key', tmp/'server.csr'
    run('openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=HuntWick fixture root',
        '-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign',
        '-keyout',ca_key,'-out',ca,stderr=subprocess.DEVNULL)
    run('openssl','req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=localhost',
        '-keyout',pem,'-out',csr,stderr=subprocess.DEVNULL)
    extensions = tmp/'server.ext'
    extensions.write_text('basicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\n'
                          'subjectAltName=DNS:localhost,IP:127.0.0.1\n')
    run('openssl','x509','-req','-in',csr,'-CA',ca,'-CAkey',ca_key,'-CAcreateserial',
        '-days','1','-extfile',extensions,'-out',cert,stderr=subprocess.DEVNULL)
    run('openssl','verify','-purpose','sslserver','-verify_ip','127.0.0.1','-CAfile',ca,cert)

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
        # The source bundle already locks reqwest through the updater. Restrict this
        # disposable client's trust store to the fixture CA for manifests and downloads.
        manifest_path=checkout/'src-tauri/Cargo.toml'
        manifest_path.write_text(manifest_path.read_text().replace('[dependencies]', '[dependencies]\n'
            'reqwest = { version = "0.13", default-features = false, features = ["rustls-no-provider"] }'))
        shutil.copyfile(ca,checkout/'src-tauri/src/fixture-ca.pem')
        run('cargo','metadata','--offline','--format-version','1','--filter-platform',TARGET,
            '--manifest-path',manifest_path,stdout=subprocess.DEVNULL)
        service.write_text(service.read_text().replace('https://github.com/ish4ra/HuntWick/releases/download/',origin)
            .replace('.updater_builder()', '.updater_builder().configure_client(|c| c.tls_certs_only(['
                     'reqwest::Certificate::from_pem(include_bytes!("fixture-ca.pem")).unwrap()]))')
            .replace('.map_err(|_| "The signed update feed could not be checked. Retry or open Releases.")',
                     '.map_err(|e| format!("fixture feed: {e:?}"))'))
        # The old client confirms its real catalog and rendered UI, then stays alive
        # for the update. Keep install_verified true so the normal exit hook permits restart.
        native=checkout/'src-tauri/src/main.rs'
        native.write_text(native.read_text().replace('    app.exit(0);', '    let _ = app;')
            .replace('    site_count: usize,\n) -> Result', '    site_count: usize,\n    step: Option<String>,\n) -> Result')
            .replace('    state.runtime.lock().unwrap().confirm_install(site_count)?;',
                     '    if let Some(step) = step { eprintln!("fixture step: {step}"); return Ok(()); }\n'
                     '    state.runtime.lock().unwrap().confirm_install(site_count)?;'))
        driver=checkout/'src/useHuntWick.ts'
        orig="void invoke('confirm_install', { siteCount })"
        assert orig in driver.read_text()
        driver.write_text(driver.read_text().replace(orig, """void (async()=>{
          const report=(step:string)=>invoke('confirm_install',{siteCount,step})
          const check=(prerelease:boolean)=>invoke<{version:string}|null>('check_update',{prerelease})
          const mustReject=async(p:Promise<unknown>)=>{
            try {await p} catch {return}
            throw Error('Expected update operation to fail')
          }
          await invoke('confirm_install',{siteCount})
          localStorage.setItem('huntwick.preferences.v1', JSON.stringify({historyEnabled:true,theme:'light'}))
          localStorage.setItem('huntwick.history.v1', JSON.stringify([{id:'fixture-preservation'}]))
          await report('missing manifest')
          await mustReject(check(false))
          await report('stable isolation')
          if (await check(false)) throw Error('Stable check accepted a prerelease')
          await report('downgrade')
          if (await check(true)) throw Error('Downgrade accepted')
          await report('unsupported platform')
          await mustReject(check(true))
          await report('invalid signature')
          const damaged=await check(true)
          if (!damaged) throw Error('Missing signature fixture')
          await mustReject(invoke('install_update',{version:damaged.version}))
          await report('signed candidate')
          const valid=await check(true)
          if (!valid) throw Error('Missing valid update')
          await invoke('install_update',{version:valid.version})
        })().catch(e=>invoke('confirm_install',{siteCount,step:'FAILED '+String(e)}))"""))
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
        env=desktop_environment(os.environ,False)
        env.update(APPIMAGE_EXTRACT_AND_RUN='1', LIBGL_ALWAYS_SOFTWARE='1', WEBKIT_DISABLE_DMABUF_RENDERER='1',
                   NO_PROXY='localhost,127.0.0.1',no_proxy='localhost,127.0.0.1',
                   XDG_CONFIG_HOME=str(tmp/'prefs'),XDG_DATA_HOME=str(tmp/'data'),XDG_CACHE_HOME=str(tmp/'cache'))
        log=tmp/'installed.log'
        with log.open('wb') as output:
            p=subprocess.Popen([installed,'--verify-install'],env=env,cwd=tmp,stdout=output,
                               stderr=subprocess.STDOUT,start_new_session=True)
        try:
            end=time.monotonic()+180
            # Only the replacement's --verify-install can print the candidate version.
            while time.monotonic()<end:
                detail=log.read_text(errors='replace')
                if f'HuntWick {VERSION} verified installed catalog and search form' in detail:
                    break
                if 'fixture step: FAILED' in detail or p.poll() not in (None,0):
                    break
                time.sleep(.5)
            else:
                detail=log.read_text(errors='replace')
            if f'HuntWick {VERSION} verified installed catalog and search form' not in detail:
                raise RuntimeError(f'Restart verification failed, requests {attempts}, exit {p.poll()}. '
                                   + ' | '.join(detail.splitlines()[-12:])[:3000])
            with installed.open('rb') as f:
                if hashlib.file_digest(f,'sha256').digest()!=expected:
                    raise RuntimeError('Installed image does not match the signed candidate.')
            if list(attempts.values()) != [4,2]:
                raise RuntimeError(f'Unexpected update feed requests: {attempts}')
            preserved={}
            for database in (tmp/'data').rglob('*.localstorage'):
                with sqlite3.connect(database) as db:
                    for name,value in db.execute('SELECT key,value FROM ItemTable'):
                        preserved[name]=value.decode('utf-16-le') if isinstance(value,bytes) else value
            if (json.loads(preserved['huntwick.preferences.v1'])['theme']!='light'
                    or json.loads(preserved['huntwick.history.v1'])[0]['id']!='fixture-preservation'):
                raise RuntimeError('Local preferences or history changed across the update.')
        finally:
            try:
                os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
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
