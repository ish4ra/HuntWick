"""Render the production logo component and styles locally with deterministic fixtures."""
import argparse
import io
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread

from PIL import Image, ImageChops
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FRAME = """<!doctype html><meta charset=utf-8><link rel=stylesheet href='/sheet.css'>
<style>body{padding:28px 32px}main{max-width:1100px;margin:auto}h1{font-size:27px;margin:0 0 18px}
section{margin:16px 0}h2{font-size:13px;margin:0 0 8px;color:var(--secondary)}
.samples{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;border:1px solid var(--line);
background:var(--line);border-radius:8px;overflow:hidden}.sample{background:var(--panel);display:flex;
gap:10px;align-items:center;padding:11px 10px;font-size:13px}.brand-mark{width:23px;height:23px}
</style><main></main><script src="/sheet.js"></script>"""


def run(destination):
    with TemporaryDirectory() as temp, sync_playwright() as pw:
        folder = Path(temp)
        builder = ROOT/'node_modules/.bin/esbuild'
        subprocess.run([str(builder),'scripts/fixtures/logo-contact-sheet.tsx','--bundle','--jsx=automatic',
                        '--external:/platforms/*','--external:/huntwick*',f'--outfile={folder}/sheet.js'],
                       cwd=ROOT, check=True)
        shutil.copytree(ROOT/'public/platforms',folder/'platforms')
        (folder/'index.html').write_text(FRAME,encoding='utf-8')
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_): pass
        with ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=temp)) as server:
            Thread(target=server.serve_forever,daemon=True).start()
            url=f'http://127.0.0.1:{server.server_port}/'
            browser=pw.chromium.launch(executable_path=shutil.which('chromium'))
            page=browser.new_page(viewport={'width':1080,'height':675},device_scale_factor=1)
            requests=[]
            page.on('request',lambda request: requests.append(request.url))
            page.goto(url)
            expect(page.locator('.sample')).to_have_count(32)
            expect(page.locator('.sample .brand-mark')).to_have_count(31)
            expect(page.locator('.sample .platform-mark')).to_have_count(1)
            assets = sorted(p.name for p in (folder/'platforms').iterdir() if p.suffix in ('.svg','.png'))
            failures = page.evaluate("""async names => {
              const failures = [];
              for (const name of names) {
                const image = new Image(); image.src = '/platforms/' + name;
                await image.decode();
                const canvas = document.createElement('canvas');
                canvas.width = canvas.height = 19;
                const context = canvas.getContext('2d', {willReadFrequently:true});
                const scale = 19 / Math.max(image.naturalWidth,image.naturalHeight);
                context.drawImage(image,0,0,image.naturalWidth*scale,image.naturalHeight*scale);
                const bytes = context.getImageData(0,0,19,19).data;
                let pixels = 0;
                for (let i=3;i<bytes.length;i+=4) if (bytes[i]>40) pixels++;
                if (pixels < 6) failures.push(name);
              }
              return failures;
            }""", assets)
            assert not failures, failures
            for theme in ('light','dark'):
                page.evaluate("t=>document.documentElement.dataset.theme=t",theme)
                # Wait for all local image and mask resources. Then measure actual
                # visible pixels, including SVG transparency and native PNG alpha.
                page.wait_for_load_state('networkidle')
                for name in ('mastodon.social','mastodon.online','mstdn.party','lemmy.ml','Laracast'):
                    expect(page.get_by_text(name,exact=True)).to_be_visible()
                for i,mark in enumerate(page.locator('.sample > :first-child').all()):
                    data=mark.screenshot()
                    before=Image.open(io.BytesIO(data)).convert('RGB')
                    size=before.size
                    mark.evaluate("e=>e.style.opacity='0'")
                    after=Image.open(io.BytesIO(mark.screenshot())).convert('RGB')
                    mark.evaluate("e=>e.style.opacity=''")
                    assert ImageChops.difference(before,after).convert('L').point(lambda x:255 if x>30 else 0).histogram()[255]>=10, (theme,i,size)
                destination.mkdir(parents=True,exist_ok=True)
                page.locator('body').screenshot(path=destination/f'logos-{theme}.png')
            assert all(request.startswith(url) for request in requests)
            browser.close()
            server.shutdown()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/platform-logos')
    run(parser.parse_args().output)
