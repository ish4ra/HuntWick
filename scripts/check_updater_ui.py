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
              if(window.previewOnly && !args.prerelease && args.discoverPreview) return {offer:null,previewVersion:'0.3.0-rc.1',feedMessage:window.feedMessage}
              if(window.current)return {offer:null,feedMessage:window.feedMessage}
              const notes=['## Search improvements','This fixture previews a signed desktop release.','',
                '- Clearer progress during long searches','- More readable platform status messages','',
                '## After installing','1. Open Settings','2. Review your saved preferences'].join(String.fromCharCode(10))
              return {offer:{version:args.prerelease?'0.3.0-rc.1':'0.2.0',notes:window.notes || notes}}
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
            preview.click()
            page.evaluate("window.previewOnly=true")
            check.click()
            expect(panel.get_by_role('status')).to_contain_text("No newer stable release is available.")
            expect(panel.get_by_role('status')).to_contain_text('HuntWick 0.3.0-rc.1 prerelease is available.')
            expect(panel.get_by_role('button', name='Check for updates', exact=True)).to_have_count(1)
            expect(install).to_have_count(0)
            page.evaluate("window.feedMessage='Stable channel: No update feed has been published.'")
            check.click()
            expect(panel.get_by_role('status')).to_contain_text('No update feed has been published')
            expect(panel.get_by_text('No newer stable release is available.',exact=False)).to_have_count(0)
            capture('prerelease-notice')
            panel.get_by_role('button',name='Check prerelease',exact=True).click()
            expect(preview).not_to_be_checked()
            expect(install).to_be_visible()
            page.evaluate("window.previewOnly=false; window.feedMessage=null")
            preview.click()
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
            page.evaluate('(notes)=>window.notes=notes',(DIST.parent/'scripts/fixtures/update/rc6-published-notes.md').read_text())
            check.click()
            expect(notes.get_by_role('listitem')).to_have_count(8)
            expect(notes.get_by_role('heading')).to_have_count(7)
            expect(notes.locator('p').first).to_have_text('0.1.0-rc.6')
            expect(notes.get_by_role('heading',name='Known limitations')).to_have_count(1)
            assert notes.locator('.release-notes').evaluate('(e)=>e.scrollHeight > e.clientHeight')
            capture('published-rc6-notes',notes)
            page.set_viewport_size({'width':700,'height':650})
            assert notes.evaluate('(e)=>e.scrollWidth <= e.clientWidth')
            notes.locator('.release-notes').scroll_into_view_if_needed()
            notes.locator('.release-notes').evaluate('(e)=>e.scrollTop=e.scrollHeight')
            expect(notes.get_by_role('heading',name='Known limitations')).to_be_in_viewport()
            page.set_viewport_size({'width':1080,'height':900})
            page.evaluate('window.notes=null')
        for failure in ['Stable channel: No update feed has been published.',
                        'Preview channel: Could not reach the update service.',
                        'Preview channel: The release metadata is invalid.']:
            page.evaluate('(s)=>{window.current=true;window.feedMessage=s}',failure)
            check.click()
            expect(panel.get_by_role('status')).to_contain_text(failure)
            expect(panel.get_by_text('No newer update is available.')).to_have_count(0)
        page.evaluate('window.current=false;window.feedMessage=null')
        page.evaluate("""() => {window.fixtureError=null; window.notes='<img src=x onerror=alert(1)>'}""")
        check.click()
        expect(panel.locator('.release-notes img')).to_have_count(0)
        expect(panel.get_by_text('<img src=x onerror=alert(1)>',exact=True)).to_be_visible()
        panel.get_by_role('button',name='Manual downloads').click()
        downloads_url = page.evaluate('window.manualUrl')
        assert downloads_url == 'https://github.com/ish4ra/HuntWick/releases' or downloads_url.startswith(
            'https://github.com/ish4ra/HuntWick/releases/tag/v')
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
    print('Chromium updater UI passed both themes, published RC.6 notes, preview notices and explicit opt-in, feed failures, progress, restart and active-search protection (fixture IPC).')

if __name__ == "__main__":
    main()
