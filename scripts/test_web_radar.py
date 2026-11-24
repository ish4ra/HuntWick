"""Chromium regression for rendered synthetic discovery events and local icons."""
import argparse
import json
import os
from pathlib import Path
import shutil

from playwright.sync_api import expect, sync_playwright


def run(port, screenshots):
    origin=f'http://127.0.0.1:{port}'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'))
        page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce',
                              http_credentials={'username':'huntwick','password':os.environ['HUNTWICK_WEB_PASSWORD']})
        def synthetic(route):
            payload=route.request.post_data_json
            events=[{'id':payload['id'],'type':'result','platform':name,'url':url+'demo','status':status}
                    for name,url,status in [('GitHub','https://www.github.com/','found'),('GitLab','https://gitlab.com/','possible')]]
            events.insert(1,events[0])
            events.append({'id':payload['id'],'type':'done'})
            route.fulfill(content_type='application/x-ndjson',body='\n'.join(map(json.dumps,events))+'\n')
        page.route('**/api/search',synthetic)
        page.goto(origin)
        for name in ('GitHub','GitLab'):page.get_by_role('checkbox',name=name,exact=True).check()
        page.locator('#username').fill('demo')
        page.locator('button[type=submit]').click()
        dots=page.locator('.discovery-dot')
        expect(dots).to_have_count(2)
        possible=page.get_by_role('button',name='GitLab · Possible Match',exact=True)
        possible.focus()
        expect(page.locator('.radar-detail')).to_contain_text('GitLab · Possible Match')
        expect(page.locator('.scope-radar.scanning')).to_have_count(0)
        for slug in ('github','gitlab'):
            assert page.request.get(origin+'/platforms/'+slug+'.svg').status==200
        if screenshots:
            page.screenshot(path=screenshots/'web-desktop.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=screenshots/'web-mobile.png',full_page=True)
        browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--screenshots',type=Path)
    args=parser.parse_args()
    run(args.port,args.screenshots)
