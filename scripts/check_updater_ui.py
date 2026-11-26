"""Check the built update interface with local Chromium and fixture IPC.

The signed AppImage installation and restart are exercised by check_appimage_update.py.
Run after npm run build with Python Playwright and Chromium available.
"""
import argparse
import functools
import http.server
import shutil
import threading
from pathlib import Path
from playwright.sync_api import expect, sync_playwright


DIST = Path(__file__).resolve().parents[1] / 'dist'

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--screenshots", type=Path)
    shots=parser.parse_args().screenshots
    with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=DIST)) as server, sync_playwright() as pw:
        threading.Thread(target=server.serve_forever,daemon=True).start()
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'))
        page=browser.new_page(viewport={'width':1080,'height':900})
        page.add_init_script("""
        window.isTauri=true
        const callbacks=[], subscriptions={}
        window.__TAURI_EVENT_PLUGIN_INTERNALS__={unregisterListener(){}}
        window.__TAURI_INTERNALS__={
          transformCallback:cb=>callbacks.push(cb)-1,
          async invoke(cmd,args){
            if(cmd==='catalog')return (await fetch('/catalog.json')).json()
            if(cmd==='plugin:event|listen'){subscriptions[args.event]=callbacks[args.handler];return args.handler}
            if(cmd==='plugin:event|unlisten')return
            if(cmd==='check_update'){
              window.lastCheck=args.prerelease
              if(window.fixtureError)throw window.fixtureError
              if(window.current)return null
              const notes=['## Search improvements','This fixture previews a signed desktop release.','',
                '- Clearer progress during long searches','- More readable platform status messages','',
                '## After installing','1. Open Settings','2. Review your saved preferences'].join(String.fromCharCode(10))
              return {version:args.prerelease?'0.3.0-rc.1':'0.2.0',notes:window.notes || notes}
            }
            if(cmd==='install_update'){
              window.emitProgress=(bytes,total)=>subscriptions['update-progress']({payload:[bytes,total]})
              window.emitProgress(5242880,10485760)
              return new Promise((_,reject)=>window.failInstall=()=>reject('Update signature verification failed. HuntWick rejected the download. Check again for a signed release.'))
            }
            if(cmd==='open_url'){window.manualUrl=args.url;return}
            if(cmd==='start_search')return
            throw Error(cmd)
          }
        }
        """)
        page.goto(f'http://127.0.0.1:{server.server_port}')
        expect(page.get_by_text('HuntWick 0.2.0 is available in Settings.')).to_be_visible()
        settings=page.get_by_role('button',name='Settings',exact=True)
        settings.click()
        panel=page.get_by_role('region',name='Software updates')
        preview=panel.get_by_role('switch',name='Include prereleases')
        check=panel.get_by_role('button',name='Check for updates',exact=True)
        install=panel.get_by_role('button',name='Install 0.3.0-rc.1 and restart')
        expect(preview).not_to_be_checked()
        assert page.evaluate('window.lastCheck') is False
        preview.click()
        page.reload()
        settings.click()
        expect(preview).to_be_checked()
        expect(install).to_be_visible()
        assert page.evaluate('window.lastCheck') is True
        for theme in ('dark','light'):
            page.get_by_label('Color theme').select_option(theme)
            def capture(name, region=panel):
                if shots:
                    region.screenshot(path=shots/theme/(name+'.png'),animations='disabled')
            page.evaluate('window.current=true')
            check.click()
            expect(panel.get_by_role('status')).to_contain_text('No newer update')
            capture('current')
            page.evaluate('window.current=false')
            check.click()
            expect(install).to_be_visible()
            capture('available')
            notes=panel.locator('.update-notes')
            expect(notes.get_by_role('list')).to_have_count(2)
            expect(notes.get_by_role('heading',name='Search improvements')).to_be_visible()
            capture('notes',notes)
            install.click()
            expect(panel.get_by_text('Restart to install HuntWick 0.3.0-rc.1?')).to_be_visible()
            capture('confirm-restart')
            panel.get_by_role('button',name='Cancel').click()
            expect(install).to_be_enabled()
            install.click()
            panel.get_by_role('button',name='Confirm restart').click()
            expect(panel.get_by_text('50% · 5.0 MiB of 10.0 MiB')).to_be_visible()
            capture('downloading')
            page.evaluate('window.emitProgress(5242880,null)')
            expect(panel.get_by_text('5.0 MiB downloaded')).to_be_visible()
            assert panel.get_by_role('progressbar').get_attribute('value') is None
            capture('downloading-unknown')
            page.evaluate('window.failInstall()')
            expect(panel.get_by_role('alert')).to_contain_text('signature verification failed')
            capture('failure')
        for failure in ['No update feed has been published for this channel yet. Check again after the next release.',
                        'Could not reach the update service. Check your connection and try Check for updates again.', 'The release metadata is invalid.']:
            page.evaluate('(s)=>window.fixtureError=s',failure)
            check.click()
            expect(panel.get_by_role('alert')).to_contain_text(failure)
        page.evaluate("""() => {window.fixtureError=null; window.notes='<img src=x onerror=alert(1)>'}""")
        check.click()
        expect(panel.locator('.release-notes img')).to_have_count(0)
        expect(panel.get_by_text('<img src=x onerror=alert(1)>',exact=True)).to_be_visible()
        panel.get_by_role('button',name='Manual downloads').click()
        assert page.evaluate('window.manualUrl').endswith('/releases/tag/v0.1.0-rc.5')
        page.get_by_role('button',name='Search',exact=True).first.click()
        page.locator('#username').fill('fixture')
        page.locator('button[type=submit]').click()
        settings.click()
        expect(install).to_be_disabled()
        preview.click()
        page.reload()
        settings.click()
        expect(preview).not_to_be_checked()
        assert page.evaluate('window.lastCheck') is False
        browser.close()
        server.shutdown()
    print('Chromium updater UI passed startup stable offer, manual preview, percentage progress, verification error recovery, release fallback and active-search interlock (fixture IPC).')

if __name__ == "__main__":
    main()
