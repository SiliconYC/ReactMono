"""P2 的真实同源 HTTP 浏览器回归：直接加载 dist/，不得把 CDN 偷换为测试替身。"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split('?',1)[0]
        if not clean.startswith('/ReactMono/'):
            return str(ROOT/'dist'/'not-found')
        return str(ROOT/'dist'/clean.removeprefix('/ReactMono/'))
    def log_message(self, *args): pass

def main():
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            launch = {'headless':True, 'args':['--no-sandbox','--disable-dev-shm-usage']}
            if os.environ.get('CHROMIUM_PATH'):
                launch['executable_path'] = os.environ['CHROMIUM_PATH']
            else:
                launch['channel'] = 'chrome'
            browser = p.chromium.launch(**launch)
            page = browser.new_page(viewport={'width':1440,'height':900})
            errors = []
            external = []
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda request:external.append(request.url) if not request.url.startswith('http://127.0.0.1:') else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
            assert page.locator('.tile').count()==24, page.locator('body').inner_text()
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            report=page.evaluate("""async()=>{
                const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
                const pause=()=>new Promise(r=>setTimeout(r,20));
                let rolls=0,turns=0,buys=0;
                for(let i=0;i<1200;i++){
                    if(document.querySelector('main[data-game-status]')?.dataset.gameStatus==='finished')
                        return {finished:true,rolls,turns,buys};
                    if(click('掷骰前进'))rolls++;
                    else if(click('购买地产'))buys++;
                    else if(click('放弃购买')){}
                    else if(click('结束当前回合'))turns++;
                    await pause();
                }
                return {finished:false,rolls,turns,buys};
            }""")
            assert report['finished'] and report['rolls']>0 and report['turns']>0 and report['buys']>0,report
            assert not errors,errors
            assert not external,external
            print('PASS: /ReactMono/ 同源 React 真实浏览器完整对局',report)
            browser.close()
    finally:
        server.shutdown()
        thread.join()

if __name__=='__main__': main()
