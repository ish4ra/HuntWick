"""Check the built update interface with local Chromium and fixture IPC.

The signed AppImage installation and restart are exercised by check_appimage_update.py.
Run after npm run build with Python Playwright and Chromium available.
"""
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
    with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=DIST)) as server, sync_playwright() as pw:
        threading.Thread(target=server.serve_forever,daemon=True).start()
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'))
        page=browser.new_page()
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
            if(cmd==='check_update')return {version:args.prerelease?'0.3.0-rc.1':'0.2.0',notes:'Test fixture'}
            if(cmd==='install_update'){
              subscriptions['update-progress']({payload:[5,10]})
              return new Promise((_,reject)=>window.failInstall=()=>reject('Fixture verification failed'))
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
        heading=page.get_by_role('heading',name='Settings',exact=True)
        panel=page.get_by_role('region',name='Software updates')
        assert heading.bounding_box()['y'] < panel.bounding_box()['y']
        expect(panel.get_by_role('switch',name='Automatic update checks')).to_be_visible()
        page.get_by_role('button',name='Check prereleases').click()
        install=page.get_by_role('button',name='Install 0.3.0-rc.1 and restart')
        install.click()
        page.get_by_role("button",name="Confirm restart").click()
        expect(page.get_by_text('50% downloaded')).to_be_visible()
        page.evaluate('window.failInstall()')
        expect(page.get_by_text('Fixture verification failed')).to_be_visible()
        expect(install).to_have_count(0)
        page.get_by_role('button',name='Manual downloads').click()
        assert page.evaluate('window.manualUrl') .endswith('/docs/rc4-acceptance.md')
        page.get_by_role('button',name='Search',exact=True).first.click()
        page.locator('#username').fill('fixture')
        page.locator('button[type=submit]').click()
        settings.click()
        heading=page.get_by_role('heading',name='Settings',exact=True)
        panel=page.get_by_role('region',name='Software updates')
        assert heading.bounding_box()['y'] < panel.bounding_box()['y']
        expect(panel.get_by_role('switch',name='Automatic update checks')).to_be_visible()
        page.get_by_role('button',name='Check prereleases').click()
        expect(install).to_be_disabled()
        browser.close()
        server.shutdown()
    print('Chromium updater UI passed startup stable offer, manual preview, percentage progress, verification error recovery, release fallback and active-search interlock (fixture IPC).')

if __name__ == "__main__":
    main()
